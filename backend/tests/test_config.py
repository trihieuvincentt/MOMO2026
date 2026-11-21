from backend.app.adapters.reputation import GoogleWebRiskProvider
from backend.app.config import get_reputation_provider


def test_reputation_provider_is_disabled_without_api_key(monkeypatch):
    monkeypatch.delenv("GOOGLE_WEB_RISK_API_KEY", raising=False)

    assert get_reputation_provider() is None


def test_reputation_provider_uses_server_side_api_key(monkeypatch):
    monkeypatch.setenv("GOOGLE_WEB_RISK_API_KEY", "configured-key")

    provider = get_reputation_provider()

    assert isinstance(provider, GoogleWebRiskProvider)
