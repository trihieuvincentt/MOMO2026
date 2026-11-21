import pytest

from backend.app.services.url_scanner import parse_submitted_url


def test_parses_http_url_into_canonical_observation():
    observation = parse_submitted_url(" HTTPS://Example.COM/path?q=1 ")

    assert observation.scheme == "https"
    assert observation.hostname == "example.com"
    assert observation.normalized_url == "https://example.com/path?q=1"
    assert observation.is_local_or_private is False


@pytest.mark.parametrize("raw", ["not a url", "javascript:alert(1)", "file:///secret.txt", "ftp://example.com/file"])
def test_rejects_malformed_or_unsupported_urls(raw: str):
    with pytest.raises(ValueError):
        parse_submitted_url(raw)


def test_rejects_credentials_in_url():
    with pytest.raises(ValueError, match="credentials"):
        parse_submitted_url("https://alice:secret@example.com/login")


@pytest.mark.parametrize(
    "raw",
    [
        "http://localhost/admin",
        "http://127.0.0.1:8080/admin",
        "http://192.168.1.20/",
        "http://[::1]/",
        "http://169.254.1.2/",
    ],
)
def test_marks_local_private_and_link_local_targets_without_resolving(raw: str):
    observation = parse_submitted_url(raw)

    assert observation.is_local_or_private is True
    assert any("local" in note.lower() or "private" in note.lower() for note in observation.notes)


def test_normalizes_idn_host_to_punycode_and_records_limitation():
    observation = parse_submitted_url("https://例え.テスト/verify")

    assert observation.hostname == "xn--r8jz45g.xn--zckzah"
    assert observation.normalized_url.startswith("https://xn--r8jz45g.xn--zckzah/")
    assert observation.notes


def test_rejects_urls_over_length_limit():
    with pytest.raises(ValueError, match="length"):
        parse_submitted_url("https://example.com/" + "a" * 2048)
