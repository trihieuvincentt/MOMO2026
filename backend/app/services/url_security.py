import ipaddress
import socket
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit, urlunsplit

from backend.app.schemas.url import URLObservation


class URLSecurityError(ValueError):
    """The submitted URL or fetch operation violates the security policy."""


@dataclass(frozen=True)
class URLSecurityPolicy:
    max_url_length: int = 2048
    max_redirects: int = 3
    max_response_bytes: int = 2 * 1024 * 1024
    connect_timeout_seconds: float = 5.0
    read_timeout_seconds: float = 15.0

    def validate_redirect_count(self, redirect_count: int) -> None:
        if redirect_count > self.max_redirects:
            raise URLSecurityError("redirect limit exceeded")


@dataclass(frozen=True)
class ResourceLimits:
    max_external_targets: int = 5
    max_pages: int = 6
    max_depth: int = 1

    def validate_external_target_count(self, count: int) -> None:
        if count > self.max_external_targets:
            raise URLSecurityError("external target limit exceeded")

    def validate_page_count(self, count: int) -> None:
        if count > self.max_pages:
            raise URLSecurityError("page limit exceeded")

    def validate_depth(self, depth: int) -> None:
        if depth > self.max_depth:
            raise URLSecurityError("crawl depth limit exceeded")


@dataclass(frozen=True)
class BrowserSecurityPolicy:
    navigation_timeout_ms: int = 15_000
    max_screenshot_bytes: int = 8 * 1024 * 1024
    max_pages: int = 6
    max_external_targets: int = 5
    max_depth: int = 1
    accept_downloads: bool = False
    allow_form_submission: bool = False


Resolver = Callable[[str], Iterable[str]]


def _resolve_addresses(hostname: str, resolver: Resolver | None) -> tuple[str, ...]:
    if resolver is not None:
        return tuple(resolver(hostname))
    try:
        return tuple({item[4][0] for item in socket.getaddrinfo(hostname, None)})
    except socket.gaierror as exc:
        raise URLSecurityError("URL hostname could not be resolved") from exc


def _is_blocked_address(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value)
    except ValueError as exc:
        raise URLSecurityError("resolved hostname returned an invalid address") from exc
    return bool(
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_unspecified
        or address.is_multicast
    )


def _parse_url(raw: str, policy: URLSecurityPolicy) -> tuple[SplitResult, str, list[str]]:
    if not isinstance(raw, str) or not raw.strip():
        raise URLSecurityError("URL is required")
    value = raw.strip()
    if len(value) > policy.max_url_length:
        raise URLSecurityError("URL length exceeds the allowed limit")
    try:
        parts = urlsplit(value)
        scheme = parts.scheme.lower()
        if scheme not in {"http", "https"}:
            raise URLSecurityError("URL scheme must be http or https")
        if parts.username is not None or parts.password is not None:
            raise URLSecurityError("URL credentials are not allowed")
        hostname = parts.hostname
        if not hostname:
            raise URLSecurityError("URL must include a hostname")
        normalized = hostname.encode("idna").decode("ascii").lower()
        port = parts.port
    except URLSecurityError:
        raise
    except (UnicodeError, ValueError) as exc:
        raise URLSecurityError("URL is malformed") from exc
    if port is not None and not 1 <= port <= 65535:
        raise URLSecurityError("URL port is invalid")
    notes: list[str] = []
    if normalized != hostname.lower():
        notes.append("Internationalized hostname normalized to punycode.")
    if parts.fragment:
        notes.append("URL fragment was removed before fetch.")
    rendered_host = f"[{normalized}]" if ":" in normalized else normalized
    netloc = rendered_host if port is None else f"{rendered_host}:{port}"
    normalized_url = urlunsplit((scheme, netloc, parts.path or "/", parts.query, ""))
    return parts, normalized, notes


def validate_fetch_target(
    raw: str,
    *,
    policy: URLSecurityPolicy | None = None,
    resolver: Resolver | None = None,
) -> URLObservation:
    policy = policy or URLSecurityPolicy()
    _, hostname, notes = _parse_url(raw, policy)
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise URLSecurityError("local targets are not allowed")
    addresses = _resolve_addresses(hostname, resolver)
    if any(_is_blocked_address(address) for address in addresses):
        raise URLSecurityError("private or local target is not allowed")
    parts = urlsplit(raw.strip())
    port = parts.port
    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    netloc = rendered_host if port is None else f"{rendered_host}:{port}"
    return URLObservation(
        normalized_url=urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, "")),
        hostname=hostname,
        scheme=parts.scheme.lower(),
        notes=notes,
        is_local_or_private=False,
    )


def validate_redirect_target(raw: str, **kwargs) -> URLObservation:
    return validate_fetch_target(raw, **kwargs)


def bounded_response_body(body: bytes, *, max_bytes: int) -> bytes:
    if len(body) > max_bytes:
        raise URLSecurityError("response body exceeds the allowed limit")
    return body
