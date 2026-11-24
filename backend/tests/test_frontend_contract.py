from pathlib import Path


FRONTEND = Path(__file__).parents[2] / "frontend"
INDEX = (FRONTEND / "index.html").read_text(encoding="utf-8")
APP = (FRONTEND / "app.js").read_text(encoding="utf-8")


def test_scanner_workflows_use_expected_api_contracts():
    assert "/api/v1/message/analyze" in APP
    assert "JSON.stringify({text})" in APP
    assert "/api/v1/url/analyze" in APP
    assert "JSON.stringify({url})" in APP
    assert "findings" in APP
    assert "limitations" in APP


def test_ocr_workflow_has_review_source_notice_and_explicit_confirmation():
    assert "/api/v1/ocr/extract" in APP
    assert "FormData" in APP
    assert "ocr_source" in APP
    assert "provider_notice" in APP
    assert 'id="ocr-text"' in INDEX
    assert 'id="ocr-confirm"' in INDEX
    assert "Nothing is scanned until you confirm" in INDEX
    assert "ocrConfirm.addEventListener" in APP
