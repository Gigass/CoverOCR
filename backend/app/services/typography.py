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
        
        # Load ML model for point size prediction
        self.ml_model = None
        self.ml_feature_cols = None
        try:
            import pickle
            from pathlib import Path
            model_path = Path("models/point_size_model/xgboost_model.pkl")
            if model_path.exists():
                with open(model_path, 'rb') as f:
                    model_data = pickle.load(f)
                    self.ml_model = model_data['model']
                    self.ml_feature_cols = model_data['feature_cols']
                print("[TypographyEstimator] ML model loaded successfully.")
        except Exception as e:
            print(f"[TypographyEstimator] Failed to load ML model: {e}")

    def estimate(
        self,
        text: str,
        crop: np.ndarray,
        box: list[list[float]],
        image_width: int,
        book_size: str = "16k",
        anchor_height: Optional[float] = None,
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
        x_coords = [p[0] for p in box]
        pixel_height = (max(y_coords) - min(y_coords))
        pixel_width = (max(x_coords) - min(x_coords))
        
        # Try ML model first (if available and anchor is provided)
        if self.ml_model and anchor_height and anchor_height > 0:
            try:
                # Prepare features (must match training features)
                features = {
                    'bbox_height': pixel_height,
                    'bbox_width': pixel_width,
                    'image_width': image_width,
                    'text_length': len(text.strip()),
                    'is_chinese': int(any('\u4e00' <= ch <= '\u9fff' for ch in text)),
                    'is_all_caps': int(text.strip().isupper() and text.strip().isascii()),
                    'is_title_case': int(text.strip()[0].isupper() and not text.strip().isupper() and text.strip().isascii()) if text.strip() else 0,
                    'height_ratio_to_anchor': pixel_height / anchor_height,
                    'relative_height': pixel_height / image_width if image_width > 0 else 0,
                    'aspect_ratio': pixel_width / pixel_height if pixel_height > 0 else 0,
                }
                
                # Create feature vector in correct order
                import pandas as pd
                feature_vector = pd.DataFrame([features])[self.ml_feature_cols]
                
                # Predict
                point_size = float(self.ml_model.predict(feature_vector)[0])
                
            except Exception as e:
                print(f"[TypographyEstimator] ML prediction failed: {e}, falling back to rule-based")
                point_size = self._fallback_point_size(text, pixel_height, image_width, book_size)
        else:
            # Fallback to rule-based approach
            point_size = self._fallback_point_size(text, pixel_height, image_width, book_size)

        # Round to nearest 0.5
        raw_point_size = round(point_size * 2) / 2

        # 3. Map to Size Name & Snap to Standard Size
        # Instead of just finding the name, we also snap the point_size to the standard size
        # if it's close enough (e.g. within 1.5pt)
        size_name, snapped_size = self._get_closest_size(raw_point_size)
        
        # Use snapped size if found, otherwise use raw
        final_point_size = snapped_size if snapped_size > 0 else raw_point_size

        return TypographyResult(
            font_family=font_family,
            font_size_name=size_name,
            point_size=final_point_size,
            confidence=confidence,
        )

    def _get_closest_size(self, point_size: float) -> Tuple[str, float]:
        """Find the closest standard Chinese font size name and value."""
        closest_name = "未知"
        closest_size = 0.0
        min_diff = float("inf")

        for name, size in self.FONT_SIZE_MAPPING.items():
            diff = abs(size - point_size)
            if diff < min_diff:
                min_diff = diff
                closest_name = name
                closest_size = size
        
        # If difference is too large (> 2.0pt), maybe it's just a custom size
        # Relaxed threshold from 5 to 2.0 to encourage snapping
        if min_diff > 2.0:
            return "自定义", 0.0
            
        return closest_name, closest_size

    def _fallback_point_size(self, text: str, pixel_height: float, image_width: int, book_size: str) -> float:
        """Fallback rule-based point size estimation."""
        book_width_inch = self.BOOK_SIZES.get(book_size, 7.28)
        
        # Dynamic k-factor based on text characteristics
        k_factor = 33.0
        clean_text = text.strip()
        length = len(clean_text)
        
        if "人工智能" in clean_text or "机器学习" in clean_text:
            k_factor = 30.0
        elif clean_text and clean_text[0].isupper() and not clean_text.isupper() and clean_text.isascii():
            k_factor = 35.0
        elif clean_text.isupper() and clean_text.isascii():
            k_factor = 28.5
        elif length > 8 and not clean_text.isascii():
            k_factor = 37.5
        
        if image_width > 0:
            term = (pixel_height / image_width) * book_width_inch
            return k_factor * term
        else:
            return pixel_height * (k_factor / 72.0)
