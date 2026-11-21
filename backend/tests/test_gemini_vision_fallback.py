import json

import pytest

from backend.app.adapters.gemini_vision import GeminiVisionExtractor


def test_gemini_vision_returns_extracted_text_and_provider_notice():
    calls = []

    def transport(method, url, headers, body, timeout):
        payload = json.loads(body)
        calls.append(payload)
        return 200, json.dumps({
            "candidates": [{"content": {"parts": [{"text": '{"text":"Hello world","warnings":[]}'}]}}]
        }).encode()

    result = GeminiVisionExtractor("test-key", transport=transport).extract(b"fake-image", "en")

    assert result.ocr_source == "gemini_vision"
    assert result.text == "Hello world"
    assert result.provider_notice
    assert "scam" not in calls[0]["contents"][0]["parts"][0]["text"].lower()
    assert calls[0]["contents"][0]["parts"][1]["inline_data"]["data"]


def test_gemini_vision_handles_malformed_output_as_uncertain():
    def transport(method, url, headers, body, timeout):
        return 200, json.dumps({
            "candidates": [{"content": {"parts": [{"text": "not json"}]}}]
        }).encode()

    with pytest.raises(ValueError, match="OCR response"):
        GeminiVisionExtractor("test-key", transport=transport).extract(b"image", None)


def test_gemini_vision_provider_failure_is_not_hidden_as_success():
    def transport(method, url, headers, body, timeout):
        raise TimeoutError("timeout")

    with pytest.raises(TimeoutError):
        GeminiVisionExtractor("test-key", transport=transport).extract(b"image", None)
