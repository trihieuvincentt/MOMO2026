import json
from urllib.parse import parse_qs

import pytest

from backend.app.adapters.reputation import (
    MultiSourceReputationProvider,
    ReputationLookup,
    ReputationProviderUnavailable,
    URLhausProvider,
    VirusTotalProvider,
)


def test_virustotal_maps_multi_engine_malicious_stats():
    calls = []

    def transport(method, url, headers, body, timeout):
        calls.append((method, url, headers, body, timeout))
        return 200, json.dumps({"data": {"attributes": {"last_analysis_stats": {"malicious": 3, "suspicious": 1}}}}).encode()

    result = VirusTotalProvider("vt-key", transport=transport).lookup("https://example.com/login")

    assert result.matched is True
    assert result.source == "virustotal"
    assert "3 malicious" in result.details
    assert calls[0][0] == "GET"
    assert calls[0][2]["x-apikey"] == "vt-key"


def test_virustotal_no_record_is_not_a_safety_claim():
    def transport(method, url, headers, body, timeout):
        return 404, b"{}"

    result = VirusTotalProvider("vt-key", transport=transport).lookup("https://example.com")

    assert result == ReputationLookup(
        matched=False,
        source="virustotal",
        details="No VirusTotal analysis record was found.",
    )


def test_urlhaus_posts_only_to_urlhaus_and_maps_known_malware_url():
    calls = []

    def transport(method, url, headers, body, timeout):
        calls.append((method, url, headers, body, timeout))
        return 200, json.dumps({"query_status": "ok", "url_status": "online", "threat": "malware_download", "tags": ["exe"]}).encode()

    result = URLhausProvider("urlhaus-key", transport=transport).lookup("https://evil.example/payload.exe")

    assert result.matched is True
    assert result.source == "urlhaus"
    assert "malware_download" in result.details
    assert calls[0][0] == "POST"
    assert calls[0][2]["Auth-Key"] == "urlhaus-key"
    assert parse_qs(calls[0][3].decode())["url"] == ["https://evil.example/payload.exe"]


def test_urlhaus_no_results_is_not_a_safety_claim():
    def transport(method, url, headers, body, timeout):
        return 200, b'{"query_status":"no_results"}'

    result = URLhausProvider("urlhaus-key", transport=transport).lookup("https://example.com")

    assert result.matched is False
    assert result.source == "urlhaus"


def test_multi_source_provider_preserves_both_sources_and_partial_failure():
    def vt_transport(method, url, headers, body, timeout):
        return 200, b'{"data":{"attributes":{"last_analysis_stats":{"malicious":1,"suspicious":0}}}}'

    def urlhaus_transport(method, url, headers, body, timeout):
        raise ReputationProviderUnavailable("URLhaus unavailable")

    result = MultiSourceReputationProvider(
        [
            VirusTotalProvider("vt-key", transport=vt_transport),
            URLhausProvider("urlhaus-key", transport=urlhaus_transport),
        ]
    ).lookup("https://example.com")

    assert result.matched is True
    assert result.sources == ("virustotal",)
    assert "URLhaus" in " ".join(result.limitations)


@pytest.mark.parametrize("provider", [VirusTotalProvider, URLhausProvider])
def test_provider_rejects_missing_api_key(provider):
    with pytest.raises(ValueError, match="API key"):
        provider("")
