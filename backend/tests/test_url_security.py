import pytest

from backend.app.services.url_security import (
    BrowserSecurityPolicy,
    ResourceLimits,
    URLSecurityError,
    URLSecurityPolicy,
    bounded_response_body,
    validate_fetch_target,
    validate_redirect_target,
)


def test_fetch_target_rejects_dns_name_resolving_to_private_address():
    def resolver(hostname: str):
        return ["203.0.113.10", "192.168.1.10"]

    with pytest.raises(URLSecurityError, match="private"):
        validate_fetch_target("https://example.com/page", resolver=resolver)


def test_fetch_target_allows_public_dns_addresses():
    observation = validate_fetch_target(
        "https://example.com/page#fragment",
        resolver=lambda hostname: ["93.184.216.34"],
    )

    assert observation.normalized_url == "https://example.com/page"
    assert observation.hostname == "example.com"


def test_redirect_target_is_checked_with_same_ssrf_policy():
    with pytest.raises(URLSecurityError, match="private"):
        validate_redirect_target(
            "http://127.0.0.1/admin",
            resolver=lambda hostname: ["127.0.0.1"],
        )


def test_redirect_limit_is_enforced():
    policy = URLSecurityPolicy(max_redirects=2)

    with pytest.raises(URLSecurityError, match="redirect"):
        policy.validate_redirect_count(3)


def test_response_body_limit_rejects_oversized_content():
    with pytest.raises(URLSecurityError, match="response"):
        bounded_response_body(b"12345", max_bytes=4)


def test_resource_limits_reject_excess_external_targets():
    limits = ResourceLimits(max_external_targets=3)

    with pytest.raises(URLSecurityError, match="external target"):
        limits.validate_external_target_count(4)


def test_browser_policy_disables_downloads_and_sensitive_actions():
    policy = BrowserSecurityPolicy()

    assert policy.accept_downloads is False
    assert policy.allow_form_submission is False
    assert policy.max_pages == 6
