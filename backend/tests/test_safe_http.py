import pytest

from backend.app.services.safe_http import (
    SafeHTTPClient,
    SafeHTTPError,
    is_allowed_content_type,
    validate_redirect_chain,
)
from backend.app.services.url_security import URLSecurityPolicy


def test_redirect_chain_rejects_private_destination():
    with pytest.raises(SafeHTTPError, match="private"):
        validate_redirect_chain(
            ["https://example.com", "http://127.0.0.1/admin"],
            resolver=lambda hostname: ["127.0.0.1"],
        )


def test_redirect_chain_rejects_too_many_hops():
    with pytest.raises(SafeHTTPError, match="redirect"):
        validate_redirect_chain(
            ["https://example.com/0", "https://example.com/1", "https://example.com/2", "https://example.com/3"],
            max_redirects=2,
            resolver=lambda hostname: ["93.184.216.34"],
        )


def test_content_type_policy_allows_html_and_rejects_downloadable_content():
    assert is_allowed_content_type("text/html; charset=utf-8")
    assert is_allowed_content_type("application/xhtml+xml")
    assert not is_allowed_content_type("application/octet-stream")
    assert not is_allowed_content_type("application/pdf")


def test_client_resolves_relative_redirect_before_validation():
    responses = iter([(302, "", b"", "/final"), (200, "text/html", b"<html />", None)])

    def transport(url, timeout, max_bytes):
        return next(responses)

    client = SafeHTTPClient(transport=transport, resolver=lambda hostname: ["93.184.216.34"])
    status, content_type, body, chain = client.get("https://example.com/start")

    assert status == 200
    assert chain == ["https://example.com/start", "https://example.com/final"]


def test_client_rejects_oversized_response_from_transport():
    def transport(url, timeout, max_bytes):
        return 200, "text/html", b"x" * (max_bytes + 1), None

    client = SafeHTTPClient(
        policy=URLSecurityPolicy(max_response_bytes=4),
        transport=transport,
        resolver=lambda hostname: ["93.184.216.34"],
    )

    with pytest.raises(SafeHTTPError, match="response"):
        client.get("https://example.com")


def test_client_requires_public_target_before_transport():
    calls = []

    class Transport:
        def __call__(self, url, timeout, max_bytes):
            calls.append(url)
            return 200, "text/html", b"<html />", None

    client = SafeHTTPClient(transport=Transport(), resolver=lambda hostname: ["127.0.0.1"])
    with pytest.raises(SafeHTTPError, match="private"):
        client.get("https://example.com")
    assert calls == []
