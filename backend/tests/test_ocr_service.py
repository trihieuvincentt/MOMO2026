import pytest

from backend.app.schemas.ocr import OCRSource
from backend.app.services.ocr_service import extract_text_from_image


class SuccessfulPaddle:
    def extract(self, image_path, language_hint=None):
        return {"text": "Paddle extracted text", "warnings": []}


class FailingPaddle:
    def extract(self, image_path, language_hint=None):
        raise RuntimeError("engine unavailable")


class SuccessfulGeminiVision:
    def __init__(self):
        self.received = []

    def extract(self, image_bytes, language_hint=None):
        self.received.append(image_bytes)
        return {"text": "Gemini extracted text", "warnings": ["Some text may be uncertain"]}


def test_ocr_service_uses_paddle_first_without_gemini_notice(tmp_path):
    image = b"test-image-bytes"

    result = extract_text_from_image(
        image,
        filename="sample.png",
        language_hint="en",
        temp_dir=tmp_path,
        paddle_engine=SuccessfulPaddle(),
        gemini_engine=None,
        image_validator=lambda data: ("image/png", 10, 10),
    )

    assert result.ocr_source == OCRSource.PADDLEOCR
    assert result.extracted_text == "Paddle extracted text"
    assert result.provider_notice is None
    assert list(tmp_path.iterdir()) == []


def test_ocr_service_falls_back_to_gemini_after_paddle_failure(tmp_path):
    image = b"test-image-bytes"
    gemini = SuccessfulGeminiVision()

    result = extract_text_from_image(
        image,
        filename="sample.png",
        language_hint="vi",
        temp_dir=tmp_path,
        paddle_engine=FailingPaddle(),
        gemini_engine=gemini,
        image_validator=lambda data: ("image/png", 10, 10),
    )

    assert result.ocr_source == OCRSource.GEMINI_VISION
    assert result.extracted_text == "Gemini extracted text"
    assert "sent to Gemini" in result.provider_notice
    assert gemini.received == [image]
    assert list(tmp_path.iterdir()) == []


def test_ocr_service_returns_manual_entry_warning_when_both_engines_unavailable(tmp_path):
    result = extract_text_from_image(
        b"test-image-bytes",
        filename="sample.png",
        language_hint=None,
        temp_dir=tmp_path,
        paddle_engine=FailingPaddle(),
        gemini_engine=None,
        image_validator=lambda data: ("image/png", 10, 10),
    )

    assert result.status == "unavailable"
    assert any("manual" in warning.lower() for warning in result.warnings)


def test_ocr_rejects_invalid_image_before_any_provider_call(tmp_path):
    gemini = SuccessfulGeminiVision()

    with pytest.raises(ValueError, match="image"):
        extract_text_from_image(
            b"not-an-image",
            filename="bad.png",
            language_hint=None,
            temp_dir=tmp_path,
            paddle_engine=SuccessfulPaddle(),
            gemini_engine=gemini,
            image_validator=lambda data: (_ for _ in ()).throw(ValueError("Invalid image content")),
        )

    assert gemini.received == []
    assert list(tmp_path.iterdir()) == []
