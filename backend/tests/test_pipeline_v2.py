import pytest
from unittest.mock import MagicMock, patch
import numpy as np
from app.services.pipeline import InferencePipeline
from app.services.ocr_service import OCRTextRegion

def test_pipeline_v2_integration():
    # Mock OCRService
    with patch("app.services.pipeline.OCRService") as MockOCRService:
        mock_ocr_instance = MockOCRService.return_value
        # Return one dummy region
        dummy_crop = np.zeros((100, 100, 3), dtype=np.uint8)
        # Box: 100x100 square starting at 0,0
        dummy_box = [[0.0, 0.0], [100.0, 0.0], [100.0, 100.0], [0.0, 100.0]]
        
        mock_ocr_instance.parse.return_value = [
            OCRTextRegion(
                text="Test Text",
                confidence=0.99,
                box=dummy_box,
                crop=dummy_crop
            )
        ]

        # Mock FontClassifier inside TypographyEstimator
        # We need to patch where TypographyEstimator imports FontClassifier
        with patch("app.services.typography.FontClassifier") as MockFontClassifier:
            mock_font_instance = MockFontClassifier.return_value
            mock_font_instance.predict.return_value = ("宋体", 0.95)

            # Initialize pipeline
            pipeline = InferencePipeline()
            
            # Mock _decode_image to return a dummy image for width calculation
            mock_ocr_instance._decode_image.return_value = np.zeros((1000, 1000, 3), dtype=np.uint8)

            # Run pipeline (private method _run_pipeline for direct testing)
            # We can't easily call _process because it's async and background.
            # But we can call _run_pipeline directly.
            
            result = pipeline._run_pipeline("req-123", b"dummy_bytes", "16k", 0.0)
            
            assert len(result.texts) == 1
            text_result = result.texts[0]
            
            assert text_result.content == "Test Text"
            assert text_result.font == "宋体"
            # Calculation with dynamic DPI:
            # Image Width = 1000px. Book Size = 16k (7.28 inch).
            # DPI = 1000 / 7.28 = 137.36
            # Box Height = 100px.
            # Char Height = 100 * 0.8 = 80px.
            # Point Size = 80 * (72 / 137.36) = 80 * 0.524 = 41.93
            # Round to nearest 0.5 => 42.0
            # 42.0 corresponds to "初号" in mapping.
            
            assert text_result.point_size == 42.0
            assert text_result.font_size_name == "初号"
            assert text_result.formatted_typography == "【初号，宋体，固定值 42.0 磅】"
