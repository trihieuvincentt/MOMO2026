import json

from backend.app.adapters.gemini_visual import GeminiVisualAnalyzer


def test_gemini_visual_analyzer_returns_structured_visual_result():
    def transport(method, url, headers, body, timeout):
        assert method == "POST"
        assert b"brand_impersonation" in body
        return 200, json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps({"site_type": "banking", "detected_brands": ["Example Bank"], "forms": [{"purpose": "login", "fields": ["username", "password", "otp"]}], "indicators": [{"category": "brand_impersonation", "description": "The page imitates a bank login.", "confidence": 0.91}], "sensitive_data_requested": ["password", "otp"], "limitations": []})}]}}]}).encode()

    analyzer = GeminiVisualAnalyzer("test-key", transport=transport)
    result = analyzer.analyze(b"PNG", mime_type="image/png", context="Claimed brand: Example Bank")

    assert result.site_type == "banking"
    assert result.detected_brands == ["Example Bank"]
    assert result.forms[0].fields == ["username", "password", "otp"]
    assert result.indicators[0].confidence == 0.91
    assert "password" in result.sensitive_data_requested


def test_visual_analyzer_rejects_malformed_provider_output():
    def transport(method, url, headers, body, timeout):
        return 200, b'{"candidates":[{"content":{"parts":[{"text":"not-json"}]}}]}'

    analyzer = GeminiVisualAnalyzer("test-key", transport=transport)

    try:
        analyzer.analyze(b"PNG", mime_type="image/png")
    except RuntimeError as exc:
        assert "structured" in str(exc).lower()
    else:
        raise AssertionError("malformed visual output must fail")
