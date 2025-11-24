#!/usr/bin/env python3
"""
批量运行 PaddleOCR，生成标注 JSON。

两种模式：
1) 纯 OCR：只写文本和 bbox，字体/字号字段留空或 0。
2) 模板合并：提供一个已有模板 JSON（字体/字号正确但 bbox=0），
   脚本按文本匹配 OCR 结果填充 bbox，同时保留模板里的字体/字号。

用法示例：
  # 纯 OCR（默认）
  python scripts/auto_bbox_dataset.py --images-dir data/aiphoto --output data/annotations/auto_bbox.json

  # 模板合并（推荐你提供模板）
  python scripts/auto_bbox_dataset.py \\
      --images-dir data/aiphoto \\
      --output data/annotations/auto_bbox_with_fonts.json \\
      --template path/to/your_template.json

说明：
- 复用 backend/app/services/ocr_service.py
- image_path 写成 images/<文件名> 以兼容既有数据格式，check_dataset 会按文件名匹配
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import sys

from PIL import Image
from rapidfuzz import fuzz, process

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.services.ocr_service import OCRService


def iter_images(images_dir: Path) -> Iterable[Path]:
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp", ".JPG", ".JPEG"}
    for path in sorted(images_dir.iterdir()):
        if path.suffix in exts and path.is_file():
            yield path


def box_to_bbox(box: Sequence[Sequence[float]], image_width: int | None = None, image_height: int | None = None) -> List[int]:
    xs = [pt[0] for pt in box]
    ys = [pt[1] for pt in box]
    x_min = int(min(xs))
    x_max = int(max(xs))
    y_min = int(min(ys))
    y_max = int(max(ys))

    if image_width is not None:
        x_min = max(0, min(x_min, image_width - 1))
        x_max = max(x_min + 1, min(x_max, image_width))
    if image_height is not None:
        y_min = max(0, min(y_min, image_height - 1))
        y_max = max(y_min + 1, min(y_max, image_height))

    return [x_min, y_min, x_max, y_max]


def confidence_level(score: float) -> str:
    if score >= 0.9:
        return "high"
    if score >= 0.7:
        return "medium"
    return "low"


def load_template(template_path: Path) -> Dict[str, dict]:
    """按图片 stem 映射模板条目，方便匹配实际文件名。"""
    with template_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    mapping: Dict[str, dict] = {}
    for img_data in data.get("images", []):
        stem = Path(img_data["image_path"]).stem
        mapping[stem] = img_data
    return mapping


def match_template_annotations(
    ocr_regions: List,
    template_annotations: List[dict],
    image_width: int,
    image_height: int,
) -> Tuple[List[dict], List[int]]:
    """
    将模板中的文本与 OCR 结果做模糊匹配，返回 (填充后的标注, 未匹配 OCR 索引列表)
    """
    ocr_texts = [r.text for r in ocr_regions]
    filled_annotations: List[dict] = []

    for ann in template_annotations:
        target_text = ann.get("text", "")
        if not ocr_regions:
            filled_annotations.append(
                {
                    "id": ann.get("id", len(filled_annotations)),
                    "text": target_text,
                    "bbox": ann.get("bbox", [0, 0, 0, 0]),
                    "font_family": ann.get("font_family", ""),
                    "font_size_name": ann.get("font_size_name", ""),
                    "point_size": ann.get("point_size", 0),
                    "confidence": ann.get("confidence", "low"),
                    "notes": f"{ann.get('notes', '')} | ocr_match=none".strip(" |"),
                }
            )
            continue

        # 允许复用 OCR 结果，直接在全部 OCR 文本中找最相似
        candidate_indices = list(range(len(ocr_texts)))
        choices = [ocr_texts[i] for i in candidate_indices]
        match = process.extractOne(
            target_text,
            choices,
            scorer=fuzz.token_sort_ratio,
        )
        if match:
            matched_text, score, choice_idx = match
            idx = candidate_indices[choice_idx]
            region = ocr_regions[idx]
            bbox = box_to_bbox(region.box, image_width, image_height)
            filled_annotations.append(
                {
                    "id": ann.get("id", len(filled_annotations)),
                    "text": target_text,  # 保留模板文本
                    "bbox": bbox,
                    "font_family": ann.get("font_family", ""),
                    "font_size_name": ann.get("font_size_name", ""),
                    "point_size": ann.get("point_size", 0),
                    "confidence": ann.get("confidence", confidence_level(region.confidence)),
                    "notes": f"{ann.get('notes', '')} | ocr_match={matched_text} score={score} conf={region.confidence:.4f}".strip(" |"),
                }
            )
            continue

        # 未匹配到
        filled_annotations.append(
            {
                "id": ann.get("id", len(filled_annotations)),
                "text": target_text,
                "bbox": ann.get("bbox", [0, 0, 0, 0]),
                "font_family": ann.get("font_family", ""),
                "font_size_name": ann.get("font_size_name", ""),
                "point_size": ann.get("point_size", 0),
                "confidence": ann.get("confidence", "low"),
                "notes": f"{ann.get('notes', '')} | ocr_match=none".strip(" |"),
            }
        )

    unused_indices: List[int] = []
    return filled_annotations, unused_indices


def build_annotations(
    images_dir: Path,
    book_size: str,
    book_width_cm: float,
    template: Dict[str, dict] | None = None,
    template_apply_all: bool = False,
) -> dict:
    ocr = OCRService()
    images_data = []

    template_default = None
    if template_apply_all and template:
        # 取模板中的第一个作为默认
        template_default = next(iter(template.values()), None)

    for img_path in iter_images(images_dir):
        print(f"📷 解析 {img_path.name} ...")
        image_bytes = img_path.read_bytes()
        regions = ocr.parse(image_bytes)

        with Image.open(img_path) as im:
            width, height = im.size

        template_item = None
        if template:
            template_item = template.get(img_path.stem)
            if template_item is None and template_apply_all:
                template_item = template_default

        if template_item:
            tmpl_annotations = template_item.get("annotations", [])
            annotations, _unused = match_template_annotations(regions, tmpl_annotations, width, height)
            tmpl_book_size = template_item.get("book_size") or book_size
            tmpl_book_width_cm = template_item.get("book_width_cm") or book_width_cm
            current_book_size = tmpl_book_size
            current_book_width_cm = tmpl_book_width_cm
        else:
            annotations = []
            for idx, region in enumerate(regions):
                bbox = box_to_bbox(region.box, width, height)
                annotations.append(
                    {
                        "id": idx,
                        "text": region.text,
                        "bbox": bbox,
                        "font_family": "",
                        "font_size_name": "",
                        "point_size": 0,
                        "confidence": confidence_level(region.confidence),
                        "notes": f"ocr_confidence={region.confidence:.4f}",
                    }
                )
            current_book_size = book_size
            current_book_width_cm = book_width_cm

        images_data.append(
            {
                "image_path": f"images/{img_path.name}",
                "image_width": width,
                "image_height": height,
                "book_size": current_book_size,
                "book_width_cm": current_book_width_cm,
                "annotations": annotations,
            }
        )

    export_date = datetime.now(timezone.utc).isoformat()
    return {
        "version": "auto-bbox-v1",
        "export_date": export_date,
        "total_images": len(images_data),
        "images": images_data,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="生成只包含 bbox 的标注 JSON")
    parser.add_argument("--images-dir", default="data/aiphoto", type=Path, help="图片目录")
    parser.add_argument("--output", default="data/annotations/auto_bbox.json", type=Path, help="输出文件")
    parser.add_argument("--book-size", default="16k", help="书本开本（模板缺省时使用）")
    parser.add_argument("--book-width-cm", default=18.5, type=float, help="书本宽度（厘米）")
    parser.add_argument("--template", type=Path, help="包含正确字体/字号但 bbox=0 的模板 JSON")
    parser.add_argument("--template-apply-all", action="store_true", help="当模板缺失某张图片时，复用模板中的第一个条目")
    args = parser.parse_args()

    images_dir = args.images_dir
    if not images_dir.exists():
        raise SystemExit(f"图片目录不存在: {images_dir}")

    args.output.parent.mkdir(parents=True, exist_ok=True)

    template = load_template(args.template) if args.template else None

    dataset = build_annotations(images_dir, args.book_size, args.book_width_cm, template, args.template_apply_all)
    with args.output.open("w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！已写入 {args.output}，共 {dataset['total_images']} 张图片。")


if __name__ == "__main__":
    main()
