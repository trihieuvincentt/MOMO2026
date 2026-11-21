import sys
from types import SimpleNamespace

from backend.app.adapters.ocr_engine import PaddleOCREngine


def test_default_factory_disables_onednn_for_cpu_compatibility(monkeypatch):
    calls = []

    def paddle_ocr(**kwargs):
        calls.append(kwargs)
        return object()

    monkeypatch.setitem(sys.modules, "paddleocr", SimpleNamespace(PaddleOCR=paddle_ocr))

    PaddleOCREngine._default_factory("en")

    assert calls[0]["enable_mkldnn"] is False
