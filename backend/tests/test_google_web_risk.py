import json

import pytest

from backend.app.adapters.reputation import (
    GoogleWebRiskProvider,
    ReputationLookup,
    ReputationProviderUnavailable,
)


def test_google_web_risk_maps_threat_response_to_match():
    requests: list[tuple[str, float]] = []

    def transport(url: str, timeout: float) -> tuple[int, bytes]:
        requests.append((url, timeout))
        return 200, json.dumps({"threat": {"threatTypes": ["SOCIAL_ENGINEERING"]}}).encode()

    result = GoogleWebRiskProvider("test-key", transport=transport).lookup("https://example.com/login")

    assert result == ReputationLookup(
        matched=True,
        source="google_web_risk",
        details="Google Web Risk reported: SOCIAL_ENGINEERING.",
    )
    assert "key=test-key" in requests[0][0]
    assert "uri=https%3A%2F%2Fexample.com%2Flogin" in requests[0][0]


def test_google_web_risk_maps_empty_threat_response_to_no_match():
    def transport(url: str, timeout: float) -> tuple[int, bytes]:
        return 200, b"{}"

    result = GoogleWebRiskProvider("test-key", transport=transport).lookup("https://example.com")

    assert result.matched is False
    assert result.source == "google_web_risk"


@pytest.mark.parametrize("status", [429, 500, 503])
def test_google_web_risk_treats_provider_outage_as_unavailable(status: int):
    def transport(url: str, timeout: float) -> tuple[int, bytes]:
        return status, b"{}"

    with pytest.raises(ReputationProviderUnavailable):
        GoogleWebRiskProvider("test-key", transport=transport).lookup("https://example.com")


def test_google_web_risk_rejects_missing_api_key():
    with pytest.raises(ValueError, match="API key"):
        GoogleWebRiskProvider("")
