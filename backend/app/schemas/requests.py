from typing import List, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")


class RecognizedText(BaseModel):
    content: str
    font: Optional[str] = None
    confidence: float = 0.0
    font_confidence: Optional[float] = None


class FontSummary(BaseModel):
    font: str
    occurrences: int
    avg_confidence: float


class ResultPayload(BaseModel):
    texts: List[RecognizedText]
    fonts_summary: List[FontSummary]
    elapsed_ms: int


class ResultResponse(ResultPayload):
    request_id: str
