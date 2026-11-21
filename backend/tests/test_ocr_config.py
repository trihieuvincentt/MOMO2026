from backend.app.adapters.ocr_engine import PaddleOCREngine
from backend.app.api.routes.ocr import get_ocr_engines


def test_ocr_route_constructs_real_paddle_engine_by_default(monkeypatch):
    monkeypatch.setenv("OCR_ENGINE", "paddleocr")
    monkeypatch.setenv("GEMINI_ENABLED", "false")

    paddle, gemini = get_ocr_engines()

    assert isinstance(paddle, PaddleOCREngine)
    assert gemini is None
