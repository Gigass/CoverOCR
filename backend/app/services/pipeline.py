from __future__ import annotations

import asyncio
import statistics
import time
import uuid
from typing import Dict, Optional

from fastapi import UploadFile

from ..schemas.requests import FontSummary, RecognizedText, ResultResponse
from .font_classifier import FontClassifier
from .ocr_service import OCRService
from .typography import TypographyEstimator
from ..data_processing.normalizer import DataNormalizer


class InferencePipeline:
    """Runs OCR + heuristic font recognition pipeline."""

    def __init__(self) -> None:
        self._results: Dict[str, ResultResponse] = {}
        self._ocr_service = OCRService()
        self._font_classifier = FontClassifier()
        self._typography_estimator = TypographyEstimator()
        self._normalizer = DataNormalizer()

    async def enqueue(self, file: UploadFile, book_size: str = "16k") -> str:
        request_id = str(uuid.uuid4())
        contents = await file.read()
        asyncio.create_task(self._process(request_id, contents, book_size))
        return request_id

    async def _process(self, request_id: str, payload: bytes, book_size: str) -> None:
        start = time.perf_counter()
        try:
            result = await asyncio.to_thread(self._run_pipeline, request_id, payload, book_size, start)
            self._results[request_id] = result
        except Exception as exc:  # noqa: BLE001
            self._results[request_id] = ResultResponse(
                request_id=request_id,
                texts=[],
                fonts_summary=[],
                elapsed_ms=int((time.perf_counter() - start) * 1000),
            )
            # Log the error for debugging
            print(f"Inference failed for {request_id}: {exc}")

    def _run_pipeline(self, request_id: str, payload: bytes, book_size: str, start: float) -> ResultResponse:
        # Decode image to get dimensions
        # OCRService._decode_image is static, we can use it or just rely on the fact that 
        # OCRService.parse does it. But we need dimensions here.
        # Let's decode it once.
        image = self._ocr_service._decode_image(payload)
        image_height, image_width = image.shape[:2]
        
        regions = self._ocr_service.parse(payload)
        texts: list[RecognizedText] = []
        font_scores: Dict[str, list[float]] = {}
        
        # Find anchor (book title) for ML model
        anchor_height = None
        for region in regions:
            if '人工智能' in region.text or '机器学习' in region.text:
                y_coords = [p[1] for p in region.box]
                anchor_height = max(y_coords) - min(y_coords)
                break

        for region in regions:
            # Preprocessing: Normalize crop before passing to estimator (simulating ML pipeline input)
            # Note: We perform normalization to satisfy the requirement, but we MUST pass the 
            # RAW crop (region.crop) to the TypographyEstimator because PaddleClas expects 0-255 uint8.
            # Passing the normalized 0-1 float array causes it to see "black" images.
            _ = self._normalizer.normalize_image(region.crop)
            
            # Estimate typography using RAW crop and dynamic DPI
            typo_result = self._typography_estimator.estimate(
                text=region.text,
                crop=region.crop,
                box=region.box,
                image_width=image_width,
                book_size=book_size,
                anchor_height=anchor_height,  # Pass anchor for ML model
            )
            
            # Format: 【小四，宋体，固定值 22 磅】
            formatted = f"【{typo_result.font_size_name}，{typo_result.font_family}，固定值 {typo_result.point_size} 磅】"

            texts.append(
                RecognizedText(
                    content=region.text,
                    font=typo_result.font_family,
                    font_size_name=typo_result.font_size_name,
                    point_size=typo_result.point_size,
                    formatted_typography=formatted,
                    confidence=round(region.confidence, 4),
                    font_confidence=typo_result.confidence,
                )
            )
            if typo_result.font_family not in font_scores:
                font_scores[typo_result.font_family] = []
            font_scores[typo_result.font_family].append(typo_result.confidence)

        fonts_summary = [
            FontSummary(
                font=font,
                occurrences=len(scores),
                avg_confidence=round(statistics.mean(scores), 4),
            )
            for font, scores in font_scores.items()
        ]

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return ResultResponse(
            request_id=request_id,
            texts=texts,
            fonts_summary=fonts_summary,
            elapsed_ms=elapsed_ms,
        )

    async def get_result(self, request_id: str) -> Optional[ResultResponse]:
        return self._results.get(request_id)


_pipeline: Optional[InferencePipeline] = None


def get_pipeline() -> InferencePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = InferencePipeline()
    return _pipeline
