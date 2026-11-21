import json

import pytest

from backend.app.adapters.gemini import GeminiInvestigationModel, GeminiProviderError


def test_gemini_adapter_sends_json_request_and_parses_response():
    calls = []

    def transport(method, url, headers, body, timeout):
        calls.append((method, url, headers, json.loads(body), timeout))
        return 200, json.dumps({
            "candidates": [{"content": {"parts": [{"text": '{"summary":"ok","finding_explanations":[],"relationships":[],"unknowns":[]}'}]}}]
        }).encode()

    model = GeminiInvestigationModel("gemini-key", transport=transport)
    result = model.generate("Analyze supplied evidence")

    assert result["summary"] == "ok"
    assert calls[0][0] == "POST"
    assert "key=gemini-key" in calls[0][1]
    assert calls[0][2]["Content-Type"] == "application/json"
    assert calls[0][3]["generationConfig"]["responseMimeType"] == "application/json"


def test_gemini_adapter_rejects_missing_api_key():
    with pytest.raises(ValueError, match="API key"):
        GeminiInvestigationModel("")


def test_gemini_adapter_maps_timeout_and_http_failure():
    def failing_transport(method, url, headers, body, timeout):
        raise TimeoutError("timeout")

    with pytest.raises(GeminiProviderError):
        GeminiInvestigationModel("key", transport=failing_transport).generate("prompt")


def test_gemini_adapter_rejects_missing_candidate_text():
    def transport(method, url, headers, body, timeout):
        return 200, b'{"candidates":[]}'

    with pytest.raises(GeminiProviderError, match="candidate"):
        GeminiInvestigationModel("key", transport=transport).generate("prompt")
