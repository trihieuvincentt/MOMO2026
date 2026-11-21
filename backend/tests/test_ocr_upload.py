import json

import pytest
from fastapi.testclient import TestClient

import backend.app.api.routes.ocr as ocr_routes
from backend.app.main import app

client = TestClient(app)


def png_bytes():
    from io import BytesIO
    from PIL import Image

    output = BytesIO()
    Image.new("RGB", (4, 4), color="white").save(output, format="PNG")
    return output.getvalue()


class StubPaddle:
    def extract(self, image_path, language_hint=None):
        return {"text": "Extracted synthetic text", "warnings": []}


def test_ocr_route_returns_source_and_does_not_log_image_text(monkeypatch, capsys):
    monkeypatch.setattr(ocr_routes, "get_ocr_engines", lambda: (StubPaddle(), None))

    response = client.post(
        "/api/v1/ocr/extract",
        files={"image": ("sample.png", png_bytes(), "image/png")},
        data={"language_hint": "en"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["extracted_text"] == "Extracted synthetic text"
    assert body["ocr_source"] == "paddleocr"
    assert body["status"] == "success"
    assert "Extracted synthetic text" not in capsys.readouterr().out


def test_ocr_route_rejects_fake_image_even_when_extension_says_png():
    response = client.post(
        "/api/v1/ocr/extract",
        files={"image": ("fake.png", b"not image data", "image/png")},
    )

    assert response.status_code == 422


def test_ocr_route_returns_notice_if_gemini_receives_image(monkeypatch):
    class StubGemini:
        def extract(self, image_bytes, language_hint=None):
            return type("Result", (), {"text": "Text from image", "warnings": [], "ocr_source": "gemini_vision", "provider_notice": "Image sent to Gemini"})()

    monkeypatch.setattr(ocr_routes, "get_ocr_engines", lambda: (None, StubGemini()))
    monkeypatch.setattr(ocr_routes, "get_ocr_engines", lambda: (type("BadPaddle", (), {"extract": lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError())})(), StubGemini()))

    response = client.post(
        "/api/v1/ocr/extract",
        files={"image": ("sample.png", png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["ocr_source"] == "gemini_vision"
    assert "Gemini" in response.json()["provider_notice"]
