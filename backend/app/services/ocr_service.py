from __future__ import annotations

from dataclasses import dataclass
from typing import List, Sequence

import cv2
import numpy as np
from paddleocr import PaddleOCR


@dataclass
class OCRTextRegion:
    text: str
    confidence: float
    box: Sequence[Sequence[float]]
    crop: np.ndarray


class OCRService:
    """Wrapper around PaddleOCR for detecting and recognizing text regions."""

    def __init__(self, lang: str = "ch", use_angle_cls: bool = True) -> None:
        self._ocr = PaddleOCR(lang=lang, use_angle_cls=use_angle_cls, show_log=False)

    def parse(self, image_bytes: bytes) -> List[OCRTextRegion]:
        image = self._decode_image(image_bytes)
        result = self._ocr.ocr(image, cls=True)
        regions: List[OCRTextRegion] = []

        for line in result:
            for bbox, (text, score) in line:
                crop = self._crop_region(image, bbox)
                regions.append(
                    OCRTextRegion(
                        text=text.strip(),
                        confidence=float(score),
                        box=bbox,
                        crop=crop,
                    )
                )
        return regions

    @staticmethod
    def _decode_image(image_bytes: bytes) -> np.ndarray:
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("无法解析上传的图像，请确认文件是否为有效的 JPG/PNG。")
        return image

    @staticmethod
    def _crop_region(image: np.ndarray, bbox: Sequence[Sequence[float]]) -> np.ndarray:
        pts = np.array(bbox, dtype=np.float32)
        x_min = max(int(np.min(pts[:, 0])) - 2, 0)
        x_max = min(int(np.max(pts[:, 0])) + 2, image.shape[1])
        y_min = max(int(np.min(pts[:, 1])) - 2, 0)
        y_max = min(int(np.max(pts[:, 1])) + 2, image.shape[0])
        crop = image[y_min:y_max, x_min:x_max]
        if crop.size == 0:
            return image
        return crop
