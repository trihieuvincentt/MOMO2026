from dataclasses import dataclass

import pytest

from backend.app.schemas.finding import VerificationStatus
from backend.app.services.url_scanner import scan_url


@dataclass
class MatchProvider:
    def lookup(self, url: str):
        return {"matched": True, "source": "test-reputation", "details": "Known phishing URL"}


@dataclass
class CleanProvider:
    def lookup(self, url: str):
        return {"matched": False, "source": "test-reputation", "details": "No known match"}


@dataclass
class FailingProvider:
    error: Exception

    def lookup(self, url: str):
        raise self.error


def test_match_is_verified_and_live():
    result = scan_url("https://example.com/login", MatchProvider())

    assert result.status == "success"
    assert result.mode == "live"
    assert result.lookup_source == "test-reputation"
    assert result.findings[0].verification_status == VerificationStatus.VERIFIED_MATCH
    assert "phishing" in result.findings[0].description.lower()


def test_no_match_is_not_reported_as_safe():
    result = scan_url("https://example.com", CleanProvider())

    assert result.status == "success"
    assert result.findings[0].verification_status == VerificationStatus.NO_SIGNAL_FOUND
    assert "not a safety guarantee" in " ".join(result.limitations).lower()


def test_private_target_never_calls_provider():
    class ExplodingProvider:
        def lookup(self, url: str):
            raise AssertionError("provider must not receive private targets")

    result = scan_url("http://127.0.0.1:8080/admin", ExplodingProvider())

    assert result.status == "success"
    assert result.mode == "unavailable"
    assert result.findings[0].verification_status == VerificationStatus.UNVERIFIED


def test_unconfigured_provider_is_explicitly_unavailable():
    result = scan_url("https://example.com", None)

    assert result.status == "unavailable"
    assert result.mode == "unavailable"
    assert result.findings[0].verification_status == VerificationStatus.UNVERIFIED


@pytest.mark.parametrize("error", [TimeoutError("timed out"), RuntimeError("quota")])
def test_provider_failures_are_explicit(error: Exception):
    result = scan_url("https://example.com", FailingProvider(error))

    assert result.status in {"unavailable", "error"}
    assert result.mode in {"unavailable", "error"}
    assert result.findings[0].verification_status == VerificationStatus.UNVERIFIED


def test_fixture_result_is_labeled_and_not_presented_as_live():
    result = scan_url("https://example.com", None, fixture_mode=True)

    assert result.status == "success"
    assert result.mode == "fixture"
    assert "fixture" in " ".join(result.limitations).lower()
