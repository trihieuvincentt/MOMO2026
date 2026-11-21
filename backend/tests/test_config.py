from backend.app.adapters.reputation import MultiSourceReputationProvider
from backend.app.config import get_reputation_provider


def test_reputation_provider_is_disabled_without_api_keys(monkeypatch):
    monkeypatch.delenv("VIRUSTOTAL_API_KEY", raising=False)
    monkeypatch.delenv("URLHAUS_API_KEY", raising=False)
    monkeypatch.delenv("URLHAUS_AUTH_KEY", raising=False)

    assert get_reputation_provider() is None


def test_reputation_provider_uses_both_server_side_api_keys(monkeypatch):
    monkeypatch.setenv("VIRUSTOTAL_API_KEY", "configured-vt-key")
    monkeypatch.setenv("URLHAUS_API_KEY", "configured-urlhaus-key")

    provider = get_reputation_provider()

    assert isinstance(provider, MultiSourceReputationProvider)


def test_reputation_provider_supports_urlhaus_auth_key_alias(monkeypatch):
    monkeypatch.setenv("VIRUSTOTAL_API_KEY", "configured-vt-key")
    monkeypatch.delenv("URLHAUS_API_KEY", raising=False)
    monkeypatch.setenv("URLHAUS_AUTH_KEY", "configured-urlhaus-key")

    assert isinstance(get_reputation_provider(), MultiSourceReputationProvider)
