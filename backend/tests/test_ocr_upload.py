import pytest
from fastapi.testclient import TestClient

import backend.app.api.routes.ocr as ocr_routes
from backend.app.schemas.ocr import OCRExtraction, OCRSource, OCRStatus
from backend.app.main import app

client = TestClient(app)


def test_ocr_endpoint_runs_extraction_in_threadpool(monkeypatch):
    seen = []
    monkeypatch.setattr(ocr_routes, "get_ocr_engines", lambda: (object(), None))

    def run_in_threadpool(function, *args, **kwargs):
        seen.append(function.__name__)
        return function(*args, **kwargs)

    monkeypatch.setattr(ocr_routes, "run_in_threadpool", run_in_threadpool)

    from io import BytesIO
    from PIL import Image
    buffer = BytesIO()
    Image.new("RGB", (4, 4), "white").save(buffer, format="PNG")

    async def fake_extract(*args, **kwargs):
        return OCRExtraction(id="ocr-1", extracted_text="ok", status=OCRStatus.SUCCESS, ocr_source=OCRSource.PADDLEOCR)

    monkeypatch.setattr(ocr_routes, "extract_text_from_image", fake_extract)
    response = client.post("/api/v1/ocr/extract", files={"image": ("x.png", buffer.getvalue(), "image/png")})

    assert response.status_code == 200
    assert seen == ["fake_extract"]
