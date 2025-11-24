from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np
from .font_classifier import FontClassifier


@dataclass
class TypographyResult:
    font_family: str
    font_size_name: str
    point_size: float
    confidence: float


class TypographyEstimator:
    """
    Estimates typography attributes: Font Family, Font Size Name, and Point Size.
    """

    # Standard Chinese font sizes (simplified mapping)
    # Name -> Point Size
    FONT_SIZE_MAPPING = {
        "初号": 42,
        "小初": 36,
        "一号": 26,
        "小一": 24,
        "二号": 22,
        "小二": 18,
        "三号": 16,
        "小三": 15,
        "四号": 14,
        "小四": 12,
        "五号": 10.5,
        "小五": 9,
        "六号": 7.5,
        "小六": 6.5,
        "七号": 5.5,
        "八号": 5,
    }

    # Standard Book Sizes (Width in inches)
    # 16开 (Standard Textbook): ~18.5cm = 7.28 inch
    # A4: 21.0cm = 8.27 inch
    # 32开 (Small Book): ~13.0cm = 5.12 inch
    BOOK_SIZES = {
        "16k": 7.28,
        "a4": 8.27,
        "32k": 5.12,
    }

    def __init__(self):
        self.font_classifier = FontClassifier()

    def estimate(
        self,
        text: str,
        crop: np.ndarray,
        box: list[list[float]],
        image_width: int,
        book_size: str = "16k",
    ) -> TypographyResult:
        """
        Estimate typography attributes for a text region.

        Args:
            text: Recognized text.
            crop: Image crop of the text region.
            box: Bounding box coordinates.
            image_width: Total width of the original image (pixels).
            book_size: Key for BOOK_SIZES ("16k", "a4", "32k").

        Returns:
            TypographyResult object.
        """
        # 1. Estimate Font Family
        font_family, confidence = self.font_classifier.predict(text, crop)

        # 2. Estimate Point Size
        # Calculate box height in pixels
        y_coords = [p[1] for p in box]
        pixel_height = (max(y_coords) - min(y_coords))
        
        # Dynamic DPI Calculation
        # DPI = Image Width (px) / Book Width (inch)
        # If image_width is missing or 0, fallback to 96 DPI (though unlikely if passed correctly)
        book_width_inch = self.BOOK_SIZES.get(book_size, 7.28)
        
        if image_width > 0:
            dpi = image_width / book_width_inch
        else:
            dpi = 96.0

        # Formula: points = pixels * (72 / DPI)
        # Refinement: Character height is ~80% of box height
        estimated_char_height_px = pixel_height * 0.8
        point_size = estimated_char_height_px * (72.0 / dpi)

        # Round to nearest 0.5
        point_size = round(point_size * 2) / 2

        # 3. Map to Size Name
        size_name = self._get_closest_size_name(point_size)

        return TypographyResult(
            font_family=font_family,
            font_size_name=size_name,
            point_size=point_size,
            confidence=confidence,
        )

    def _get_closest_size_name(self, point_size: float) -> str:
        """Find the closest standard Chinese font size name."""
        closest_name = "未知"
        min_diff = float("inf")

        for name, size in self.FONT_SIZE_MAPPING.items():
            diff = abs(size - point_size)
            if diff < min_diff:
                min_diff = diff
                closest_name = name
        
        # If difference is too large (> 5pt), maybe it's just a custom size
        if min_diff > 5:
            return "自定义"
            
        return closest_name
