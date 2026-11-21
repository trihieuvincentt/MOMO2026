import io
from pathlib import Path

from PIL import Image, UnidentifiedImageError

_ALLOWED_FORMATS = {
    "PNG": ("image/png", b"\x89PNG\r\n\x1a\n"),
    "JPEG": ("image/jpeg", b"\xff\xd8\xff"),
}


def validate_image_bytes(
    image_bytes: bytes,
    *,
    max_bytes: int = 5 * 1024 * 1024,
    max_pixels: int = 20_000_000,
) -> tuple[str, int, int]:
    if not image_bytes:
        raise ValueError("Image is empty")
    if len(image_bytes) > max_bytes:
        raise ValueError("Image exceeds the maximum byte size")
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image_format = image.format
            width, height = image.size
            image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("Invalid image content") from exc
    if image_format not in _ALLOWED_FORMATS:
        raise ValueError("Only PNG and JPEG images are allowed")
    mime_type, signature = _ALLOWED_FORMATS[image_format]
    if not image_bytes.startswith(signature):
        raise ValueError("Image signature does not match its content")
    if width <= 0 or height <= 0 or width * height > max_pixels:
        raise ValueError("Image dimensions exceed the allowed pixel limit")
    return mime_type, width, height


def _extract_result(engine, image_path: Path, language_hint: str | None):
    result = engine.extract(image_path, language_hint)
    if isinstance(result, dict):
        return str(result.get("text", "")), list(result.get("warnings", []))
    return str(result.text), list(getattr(result, "warnings", []))


def _extract_gemini(engine, image_bytes: bytes, language_hint: str | None):
    result = engine.extract(image_bytes, language_hint)
    if isinstance(result, dict):
        return str(result.get("text", "")), list(result.get("warnings", []))
    return str(result.text), list(getattr(result, "warnings", []))


def extract_text_from_image(
    image_bytes: bytes,
    *,
    filename: str,
    language_hint: str | None,
    temp_dir: Path,
    paddle_engine,
    gemini_engine,
    image_validator=validate_image_bytes,
):
    from uuid import uuid4

    from backend.app.schemas.ocr import OCRExtraction, OCRSource, OCRStatus

    from backend.app.schemas.ocr import OCRExtraction, OCRSource, OCRStatus

    mime_type, _, _ = image_validator(image_bytes)
    temp_dir.mkdir(parents=True, exist_ok=True)
    suffix = ".jpg" if mime_type == "image/jpeg" else ".png"
    temp_path = temp_dir / f"ocr-{uuid4().hex}{suffix}"
    try:
        temp_path.write_bytes(image_bytes)
        try:
            text, warnings = _extract_result(paddle_engine, temp_path, language_hint)
            source = OCRSource.PADDLEOCR
            notice = None
            status = OCRStatus.SUCCESS
        except Exception:
            if gemini_engine is None:
                return OCRExtraction(
                    id=f"ocr-{uuid4().hex[:12]}",
                    extracted_text="",
                    warnings=["OCR engine unavailable. Enter or paste the text manually."],
                    status=OCRStatus.UNAVAILABLE,
                    ocr_source=OCRSource.NONE,
                )
            text, warnings = _extract_gemini(gemini_engine, image_bytes, language_hint)
            source = OCRSource.GEMINI_VISION
            notice = "PaddleOCR was unavailable; this image was sent to Gemini for text extraction."
            status = OCRStatus.SUCCESS
        if not text.strip():
            warnings.append("No readable text was extracted. Enter or paste the text manually.")
        return OCRExtraction(
            id=f"ocr-{uuid4().hex[:12]}",
            extracted_text=text,
            warnings=warnings,
            status=status,
            ocr_source=source,
            provider_notice=notice,
        )
    finally:
        temp_path.unlink(missing_ok=True)
