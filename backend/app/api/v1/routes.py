from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from fastapi.responses import JSONResponse

from ...schemas.requests import UploadResponse, ResultResponse
from ...services.pipeline import InferencePipeline, get_pipeline


router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_image(
    file: UploadFile,
    book_size: str = Form("16k"),
    pipeline: InferencePipeline = Depends(get_pipeline),
) -> UploadResponse:
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(status_code=400, detail="Unsupported file type")

    request_id = await pipeline.enqueue(file, book_size)
    return UploadResponse(request_id=request_id)


@router.get("/result/{request_id}", response_model=ResultResponse)
async def get_result(
    request_id: str,
    pipeline: InferencePipeline = Depends(get_pipeline),
) -> JSONResponse:
    result = await pipeline.get_result(request_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Result not found yet")
    return JSONResponse(content=result.model_dump())
