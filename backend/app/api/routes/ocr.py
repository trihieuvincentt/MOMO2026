import os
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from backend.app.adapters.gemini_vision import GeminiVisionExtractor
from backend.app.adapters.ocr_engine import PaddleOCREngine
from backend.app.config import get_investigation_model
from backend.app.schemas.ocr import OCRExtraction
from backend.app.services.ocr_service import extract_text_from_image

router = APIRouter(prefix="/api/v1/ocr", tags=["ocr"])
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
TEMP_UPLOAD_DIR = Path(os.getenv("OCR_TEMP_DIR", ".tmp/ocr"))


def get_ocr_engines():
    model = get_investigation_model()
    gemini = None
    if model is not None:
        gemini = GeminiVisionExtractor(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model_name=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
        )
    if os.getenv("OCR_ENGINE", "paddleocr").strip().lower() == "gemini_vision":
        return None, gemini
    return PaddleOCREngine(), gemini


@router.post("/extract", response_model=OCRExtraction)
async def extract_ocr_route(
    image: UploadFile = File(...),
    language_hint: str | None = Form(default=None, max_length=20),
) -> OCRExtraction:
    image_bytes = await image.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the maximum upload size")
    paddle, gemini = get_ocr_engines()
    try:
        return await run_in_threadpool(
            extract_text_from_image,
            image_bytes,
            filename=image.filename or "upload.png",
            language_hint=language_hint,
            temp_dir=TEMP_UPLOAD_DIR,
            paddle_engine=paddle,
            gemini_engine=gemini,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    finally:
        await image.close()
