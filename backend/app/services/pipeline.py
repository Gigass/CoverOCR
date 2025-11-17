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


class InferencePipeline:
    """Runs OCR + heuristic font recognition pipeline."""

    def __init__(self) -> None:
        self._results: Dict[str, ResultResponse] = {}
        self._ocr_service = OCRService()
        self._font_classifier = FontClassifier()

    async def enqueue(self, file: UploadFile) -> str:
        request_id = str(uuid.uuid4())
        contents = await file.read()
        asyncio.create_task(self._process(request_id, contents))
        return request_id

    async def _process(self, request_id: str, payload: bytes) -> None:
        start = time.perf_counter()
        try:
            result = await asyncio.to_thread(self._run_pipeline, request_id, payload, start)
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

    def _run_pipeline(self, request_id: str, payload: bytes, start: float) -> ResultResponse:
        regions = self._ocr_service.parse(payload)
        texts: list[RecognizedText] = []
        font_scores: Dict[str, list[float]] = {}

        for region in regions:
            font_label, font_conf = self._font_classifier.predict(region.text, region.crop)
            texts.append(
                RecognizedText(
                    content=region.text,
                    font=font_label,
                    confidence=round(region.confidence, 4),
                    font_confidence=font_conf,
                )
            )
            if font_label not in font_scores:
                font_scores[font_label] = []
            font_scores[font_label].append(font_conf)

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
