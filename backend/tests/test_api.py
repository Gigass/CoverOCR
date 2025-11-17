import time

import time
from typing import Optional

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.requests import FontSummary, RecognizedText, ResultResponse
from app.services.pipeline import get_pipeline


class DummyPipeline:
    def __init__(self) -> None:
        self._stored: Optional[ResultResponse] = None

    async def enqueue(self, file):  # type: ignore[override]
        request_id = "test-request"
        self._stored = ResultResponse(
            request_id=request_id,
            texts=[
                RecognizedText(content="Hello", font="Arial", confidence=0.91, font_confidence=0.6)
            ],
            fonts_summary=[FontSummary(font="Arial", occurrences=1, avg_confidence=0.6)],
            elapsed_ms=120,
        )
        return request_id

    async def get_result(self, request_id: str) -> Optional[ResultResponse]:  # type: ignore[override]
        return self._stored if self._stored and self._stored.request_id == request_id else None


dummy_pipeline = DummyPipeline()
app.dependency_overrides[get_pipeline] = lambda: dummy_pipeline

client = TestClient(app)


def test_upload_and_result_flow():
    resp = client.post(
        "/api/v1/upload",
        files={"file": ("demo.jpg", b"fake-image-bytes", "image/jpeg")},
    )
    assert resp.status_code == 200
    request_id = resp.json()["request_id"]

    result_resp = None
    for _ in range(3):
        result_resp = client.get(f"/api/v1/result/{request_id}")
        if result_resp.status_code == 200:
            break
        time.sleep(0.05)

    assert result_resp is not None
    assert result_resp.status_code == 200
    body = result_resp.json()
    assert body["request_id"] == request_id
    assert "texts" in body
    assert "fonts_summary" in body
