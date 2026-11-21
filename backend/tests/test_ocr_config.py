from backend.app.adapters.gemini_vision import GeminiVisionExtractor
from backend.app.api.routes.ocr import get_ocr_engines


def test_gemini_vision_engine_uses_existing_gemini_enable_and_model_settings(monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "configured-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.8-flash")

    _, vision = get_ocr_engines()

    assert isinstance(vision, GeminiVisionExtractor)
    assert vision.model_name == "gemini-3.8-flash"


def test_gemini_vision_is_not_constructed_when_disabled(monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "false")
    monkeypatch.setenv("GEMINI_API_KEY", "configured-key")

    _, vision = get_ocr_engines()

    assert vision is None
