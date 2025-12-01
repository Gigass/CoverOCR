from __future__ import annotations

import math
import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
import paddle
import paddle.nn as nn
import paddle.vision.transforms as T
from paddle.vision.models import resnet18
from paddle.inference import Config, create_predictor

# paddleclas is optional; fall back to heuristic classifier if unavailable
try:
    from paddleclas.paddleclas import check_model_file
    _PADDLECLAS_AVAILABLE = True
except Exception:  # noqa: BLE001
    _PADDLECLAS_AVAILABLE = False

MODEL_NAME = "PPLCNetV2_base"
FONT_BASE_DIR = Path("models/fonts")
GALLERY_TEXTS = ["CoverOCR", "字体识别AI", "123abc", "封面检测"]


@dataclass
class FontResource:
    key: str
    display_name: str
    filename: str
    url: str
    description: str
    path: Optional[Path] = field(default=None)


FONT_RESOURCES: Sequence[FontResource] = (
    FontResource(
        key="noto_sans_sc",
        display_name="黑体（Noto Sans SC）",
        filename="NotoSansSC-Regular.otf",
        url="https://github.com/googlefonts/noto-cjk/raw/main/Sans/OTF/SimplifiedChinese/NotoSansSC-Regular.otf",
        description="开源黑体风格字体，近似系统黑体/微软雅黑",
    ),
    FontResource(
        key="noto_serif_sc",
        display_name="宋体（Noto Serif SC）",
        filename="NotoSerifSC-Regular.otf",
        url="https://github.com/googlefonts/noto-cjk/raw/main/Serif/OTF/SimplifiedChinese/NotoSerifSC-Regular.otf",
        description="开源宋体风格字体，近似宋体/仿宋",
    ),
    FontResource(
        key="wenkai",
        display_name="楷体（霞鹜文楷）",
        filename="LXGWWenKaiLite-Regular.ttf",
        url="https://github.com/lxgw/LxgwWenKai-Lite/releases/download/v1.310/LXGWWenKaiLite-Regular.ttf",
        description="开源楷体/手写体，近似楷体",
    ),
    FontResource(
        key="roboto",
        display_name="Arial（Roboto）",
        filename="Roboto-Regular.ttf",
        url="https://github.com/google/fonts/raw/main/apache/roboto/Roboto-Regular.ttf",
        description="开源无衬线英文字体，对标 Arial",
    ),
    FontResource(
        key="playfair",
        display_name="Times（Playfair）",
        filename="PlayfairDisplay-Regular.ttf",
        url="https://github.com/google/fonts/raw/main/ofl/playfairdisplay/PlayfairDisplay-Regular.ttf",
        description="开源衬线英文字体，对标 Times New Roman",
    ),
)


class PaddleClasFeatureExtractor:
    """Minimal paddle inference runner that outputs normalized logits."""

    def __init__(self, model_name: str = MODEL_NAME) -> None:
        if not _PADDLECLAS_AVAILABLE:
            raise ImportError("paddleclas is not installed; advanced font classifier disabled")
        model_dir = Path(check_model_file("imn", model_name))
        model_file = model_dir / "inference.pdmodel"
        params_file = model_dir / "inference.pdiparams"
        config = Config(str(model_file), str(params_file))
        config.disable_gpu()
        config.set_cpu_math_library_num_threads(
            int(os.environ.get("COVEROCR_FONT_THREADS", "2"))
        )
        config.enable_memory_optim()
        config.switch_use_feed_fetch_ops(False)
        self.predictor = create_predictor(config)
        self.input_handle = self.predictor.get_input_handle(
            self.predictor.get_input_names()[0]
        )
        self.output_handle = self.predictor.get_output_handle(
            self.predictor.get_output_names()[0]
        )
        self.mean = np.array([0.485, 0.456, 0.406], dtype=np.float32).reshape((3, 1, 1))
        self.std = np.array([0.229, 0.224, 0.225], dtype=np.float32).reshape((3, 1, 1))

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        resized = cv2.resize(image, (224, 224), interpolation=cv2.INTER_AREA)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        normalized = (rgb.transpose(2, 0, 1) - self.mean) / self.std
        return normalized[np.newaxis, :]

    def extract(self, image: np.ndarray) -> Optional[np.ndarray]:
        try:
            tensor = self._preprocess(image)
        except Exception:
            return None

        self.input_handle.copy_from_cpu(tensor)
        self.predictor.run()
        output = self.output_handle.copy_to_cpu()[0]
        norm = np.linalg.norm(output)
        if norm == 0:
            return None
        return output / norm


class PaddleClasFontClassifier:
    """Use PaddleClas embeddings + synthetic gallery to classify fonts."""

    def __init__(self) -> None:
        self.font_resources = self._prepare_fonts()
        self.extractor = PaddleClasFeatureExtractor()
        self.gallery = self._build_gallery(self.font_resources)

    def _prepare_fonts(self) -> List[FontResource]:
        FONT_BASE_DIR.mkdir(parents=True, exist_ok=True)
        available: List[FontResource] = []
        for spec in FONT_RESOURCES:
            path = FONT_BASE_DIR / spec.filename
            if not path.exists():
                self._download_font(spec.url, path, spec.display_name)
            if path.exists():
                available.append(FontResource(**{**spec.__dict__, "path": path}))
        return available

    @staticmethod
    def _download_font(url: str, path: Path, display_name: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with requests.get(url, stream=True, timeout=30) as resp:
                resp.raise_for_status()
                with open(path, "wb") as out:
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            out.write(chunk)
        except Exception as exc:  # noqa: BLE001
            if path.exists():
                path.unlink(missing_ok=True)
            print(f"[FontAssets] 下载字体 {display_name} 失败：{exc}")

    def _build_gallery(self, fonts: Sequence[FontResource]) -> Dict[str, List[np.ndarray]]:
        gallery: Dict[str, List[np.ndarray]] = {}
        for spec in fonts:
            if spec.path is None:
                continue
            embeddings: List[np.ndarray] = []
            for text in GALLERY_TEXTS:
                sample = self._render_sample(spec.path, text)
                embedding = self.extractor.extract(sample)
                if embedding is not None:
                    embeddings.append(embedding)
            if embeddings:
                gallery[spec.display_name] = embeddings
        return gallery

    @staticmethod
    def _render_sample(font_path: Path, text: str) -> np.ndarray:
        img = Image.new("RGB", (256, 256), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype(str(font_path), size=88, encoding="utf-8")
        except OSError:
            font = ImageFont.load_default()
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        pos = ((256 - text_w) // 2, (256 - text_h) // 2)
        draw.text(pos, text, fill=(20, 20, 20), font=font)
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def predict(self, text: str, crop: Optional[np.ndarray]) -> Optional[Tuple[str, float]]:
        if not self.gallery or crop is None or crop.size == 0:
            return None
        embedding = self.extractor.extract(crop)
        if embedding is None:
            return None

        best_label = None
        best_score = -1.0
        for label, vectors in self.gallery.items():
            for proto in vectors:
                score = float(np.dot(embedding, proto))
                if score > best_score:
                    best_score = score
                    best_label = label
        if best_label is None:
            return None
        confidence = max(0.0, min(1.0, (best_score + 1) / 2))
        return best_label, confidence


class HeuristicFontClassifier:
    """Legacy heuristic classifier kept as fallback."""

    COMMON_CHINESE_BOLD_FONTS = ("黑体", "微软雅黑", "思源黑体")
    COMMON_CHINESE_SERIF_FONTS = ("宋体", "仿宋", "楷体")
    COMMON_LATIN_SERIF = ("Times New Roman", "Georgia")
    COMMON_LATIN_SANS = ("Arial", "Helvetica", "Roboto")

    def predict(self, text: str, crop: Optional[np.ndarray]) -> Tuple[str, float]:
        normalized = text.strip()
        if not normalized:
            return "未知字体", 0.0

        if self._contains_chinese(normalized):
            features = self._extract_basic_features(crop)
            fill_ratio = features["fill_ratio"]
            edge_ratio = features["edge_ratio"]
            serif_score = features["serif_score"]

            if fill_ratio > 0.38 or (fill_ratio > 0.32 and edge_ratio < 0.12):
                return self.COMMON_CHINESE_BOLD_FONTS[0], 0.72
            if fill_ratio > 0.33:
                return self.COMMON_CHINESE_BOLD_FONTS[1], 0.66
            if serif_score > 1.25:
                return self.COMMON_CHINESE_SERIF_FONTS[2], 0.62
            if edge_ratio > 0.2:
                return self.COMMON_CHINESE_SERIF_FONTS[1], 0.6
            return self.COMMON_CHINESE_SERIF_FONTS[0], 0.55

        uppercase_ratio = sum(1 for ch in normalized if ch.isupper()) / max(len(normalized), 1)
        features = self._extract_basic_features(crop)
        fill_ratio = features["fill_ratio"]
        serif_score = features["serif_score"]
        italic_angle = features["italic_angle"]

        if abs(italic_angle) > 10:
            return self.COMMON_LATIN_SERIF[0], 0.66
        if serif_score > 1.1 and fill_ratio < 0.22:
            return self.COMMON_LATIN_SERIF[1], 0.62
        if uppercase_ratio > 0.8 and fill_ratio > 0.26:
            return self.COMMON_LATIN_SANS[0], 0.64
        if fill_ratio > 0.28:
            return self.COMMON_LATIN_SANS[1], 0.6
        return self.COMMON_LATIN_SANS[2], 0.55

    @staticmethod
    def _contains_chinese(text: str) -> bool:
        return any("\u4e00" <= ch <= "\u9fff" for ch in text)

    @staticmethod
    def _extract_basic_features(crop: Optional[np.ndarray]) -> Dict[str, float]:
        if crop is None or crop.size == 0:
            return {"fill_ratio": 0.25, "edge_ratio": 0.1, "serif_score": 1.0, "italic_angle": 0.0}
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        fill_ratio = float(np.count_nonzero(binary < 128)) / max(binary.size, 1)
        edges = cv2.Canny(gray, 80, 160)
        edge_ratio = float(np.count_nonzero(edges)) / max(edges.size, 1)

        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        horizontal_energy = float(np.mean(np.abs(sobel_x)) + 1e-6)
        vertical_energy = float(np.mean(np.abs(sobel_y)) + 1e-6)
        serif_score = horizontal_energy / vertical_energy

        coords = np.column_stack(np.where(binary < 128))
        italic_angle = 0.0
        if coords.size > 0:
            [vx, vy, _, _] = cv2.fitLine(coords.astype(np.float32), cv2.DIST_L2, 0, 0.01, 0.01)
            italic_angle = math.degrees(math.atan2(float(vx), float(vy)))

        return {
            "fill_ratio": fill_ratio,
            "edge_ratio": edge_ratio,
            "serif_score": serif_score,
            "italic_angle": italic_angle,
        }


class CustomResNetFontClassifier:
    """Fine-tuned ResNet18 classifier for specific book cover fonts."""

    def __init__(self, model_dir: Path) -> None:
        self.model_dir = model_dir
        self.params_path = model_dir / "font_resnet18.pdparams"
        self.mapping_path = model_dir / "class_mapping.json"
        
        if not self.params_path.exists() or not self.mapping_path.exists():
            raise FileNotFoundError("Custom model files not found")
            
        with open(self.mapping_path, 'r', encoding='utf-8') as f:
            self.classes = json.load(f)
            
        # Initialize model structure
        self.model = resnet18(pretrained=False)
        in_features = self.model.fc.weight.shape[0]
        self.model.fc = nn.Linear(in_features, len(self.classes))
        
        # Load weights
        state_dict = paddle.load(str(self.params_path))
        self.model.set_state_dict(state_dict)
        self.model.eval()
        
        # Transforms (must match training)
        self.transform = T.Compose([
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        
    def predict(self, text: str, crop: Optional[np.ndarray]) -> Optional[Tuple[str, float]]:
        if crop is None or crop.size == 0:
            return None
            
        try:
            # Preprocess
            img = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            img_tensor = self.transform(img)
            img_tensor = img_tensor.unsqueeze(0)
            
            with paddle.no_grad():
                outputs = self.model(img_tensor)
                probs = paddle.nn.functional.softmax(outputs, axis=1)
                score, idx = paddle.topk(probs, k=1)
                
            label = self.classes[idx.item()]
            confidence = score.item()
            
            return label, confidence
        except Exception as e:
            print(f"[CustomFontClassifier] Prediction failed: {e}")
            return None

class FontClassifier:
    """Facade that tries PaddleClas gallery first, then falls back to heuristics."""

    def __init__(self) -> None:
        self._custom: Optional[CustomResNetFontClassifier] = None
        self._advanced: Optional[PaddleClasFeatureExtractor] = None # Deprecated/Fallback
        
        # Try loading custom model first
        try:
            custom_model_dir = Path("models/custom_font_classifier")
            if custom_model_dir.exists():
                self._custom = CustomResNetFontClassifier(custom_model_dir)
                print("[FontClassifier] 已加载微调后的 ResNet18 模型。")
        except Exception as exc:
             print(f"[FontClassifier] 加载微调模型失败: {exc}")

        if not self._custom:
            try:
                self._advanced = PaddleClasFontClassifier()
            except Exception as exc:  # noqa: BLE001
                print(f"[FontClassifier] PaddleClas 初始化失败，使用启发式策略。原因：{exc}")
        
        self._fallback = HeuristicFontClassifier()

    def predict(self, text: str, crop: Optional[np.ndarray]) -> Tuple[str, float]:
        if self._custom:
            result = self._custom.predict(text, crop)
            if result:
                return result
                
        if self._advanced:
            result = self._advanced.predict(text, crop)
            if result:
                return result
        return self._fallback.predict(text, crop)


# Override with a simplified FontClassifier that works without paddleclas on Python 3.12+
class FontClassifier:  # type: ignore[redef]
    """Tries custom model, then optional PaddleClas, then heuristics."""

    def __init__(self) -> None:
        self._custom: Optional[CustomResNetFontClassifier] = None
        self._advanced: Optional[PaddleClasFeatureExtractor] = None

        # Try loading custom fine-tuned model
        try:
            custom_model_dir = Path("models/custom_font_classifier")
            if custom_model_dir.exists():
                self._custom = CustomResNetFontClassifier(custom_model_dir)
                print("[FontClassifier] Loaded fine-tuned ResNet18 model")
        except Exception as exc:  # noqa: BLE001
            print(f"[FontClassifier] Failed to load fine-tuned model: {exc}")

        # Optional PaddleClas path
        if not self._custom and _PADDLECLAS_AVAILABLE:
            try:
                self._advanced = PaddleClasFontClassifier()
            except Exception as exc:  # noqa: BLE001
                print(f"[FontClassifier] PaddleClas init failed, using heuristics: {exc}")
        elif not _PADDLECLAS_AVAILABLE:
            print("[FontClassifier] paddleclas not available; using heuristics.")

        self._fallback = HeuristicFontClassifier()

    def predict(self, text: str, crop: Optional[np.ndarray]) -> Tuple[str, float]:
        if self._custom:
            result = self._custom.predict(text, crop)
            if result:
                return result

        if self._advanced:
            result = self._advanced.predict(text, crop)
            if result:
                return result

        return self._fallback.predict(text, crop)
