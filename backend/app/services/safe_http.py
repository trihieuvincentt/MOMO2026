import urllib.request
from collections.abc import Iterable
from typing import Protocol
from urllib.error import HTTPError
from urllib.parse import urljoin


from backend.app.services.url_security import (
    Resolver,
    URLSecurityError,
    URLSecurityPolicy,
    bounded_response_body,
    validate_redirect_target,
)


class SafeHTTPError(URLSecurityError):
    """A network request violated the safe fetch policy."""


class HTTPTransport(Protocol):
    def __call__(
        self, url: str, timeout: float, max_bytes: int
    ) -> tuple[int, str, bytes, str | None]: ...


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirectHandler)


def _urllib_transport(url: str, timeout: float, max_bytes: int) -> tuple[int, str, bytes, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "ScamGuard/1.0"}, method="GET")
    try:
        with _NO_REDIRECT_OPENER.open(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            body = bounded_response_body(response.read(max_bytes + 1), max_bytes=max_bytes)
            return int(response.status), content_type, body, response.headers.get("Location")
    except HTTPError as exc:
        if exc.code in {301, 302, 303, 307, 308}:
            return exc.code, exc.headers.get("Content-Type", ""), b"", exc.headers.get("Location")
        raise SafeHTTPError("safe HTTP request failed") from exc
    except URLSecurityError as exc:
        raise SafeHTTPError(str(exc)) from exc
    except Exception as exc:
        raise SafeHTTPError("safe HTTP request failed") from exc


def is_allowed_content_type(content_type: str) -> bool:
    media_type = content_type.split(";", 1)[0].strip().lower()
    return media_type in {"text/html", "application/xhtml+xml"}


def validate_redirect_chain(
    urls: Iterable[str],
    *,
    max_redirects: int = 3,
    resolver: Resolver | None = None,
) -> list[str]:
    values = list(urls)
    if len(values) - 1 > max_redirects:
        raise SafeHTTPError("redirect limit exceeded")
    normalized: list[str] = []
    policy = URLSecurityPolicy(max_redirects=max_redirects)
    try:
        for value in values:
            normalized.append(validate_redirect_target(value, policy=policy, resolver=resolver).normalized_url)
    except URLSecurityError as exc:
        raise SafeHTTPError(str(exc)) from exc
    return normalized


def read_bounded_body(chunks: Iterable[bytes], *, max_bytes: int) -> bytes:
    body = b""
    for chunk in chunks:
        body += chunk
        if len(body) > max_bytes:
            raise SafeHTTPError("response body exceeds the allowed limit")
    return bounded_response_body(body, max_bytes=max_bytes)


class SafeHTTPClient:
    """Fetch HTML with target, redirect, content-type, and size controls."""

    def __init__(
        self,
        *,
        policy: URLSecurityPolicy | None = None,
        transport: HTTPTransport = _urllib_transport,
        resolver: Resolver | None = None,
    ) -> None:
        self.policy = policy or URLSecurityPolicy()
        self.transport = transport
        self.resolver = resolver

    def get(self, url: str) -> tuple[int, str, bytes, list[str]]:
        try:
            current = validate_redirect_target(url, policy=self.policy, resolver=self.resolver)
        except URLSecurityError as exc:
            raise SafeHTTPError(str(exc)) from exc
        chain = [current.normalized_url]
        for _ in range(self.policy.max_redirects + 1):
            status, content_type, body, redirect_url = self.transport(
                chain[-1], self.policy.read_timeout_seconds, self.policy.max_response_bytes
            )
            if status in {301, 302, 303, 307, 308} and redirect_url:
                if len(chain) - 1 >= self.policy.max_redirects:
                    raise SafeHTTPError("redirect limit exceeded")
                target = validate_redirect_target(
                    urljoin(chain[-1], redirect_url), policy=self.policy, resolver=self.resolver
                )
                chain.append(target.normalized_url)
                continue
            if not is_allowed_content_type(content_type):
                raise SafeHTTPError("response content type is not allowed")
            try:
                bounded_body = bounded_response_body(body, max_bytes=self.policy.max_response_bytes)
            except URLSecurityError as exc:
                raise SafeHTTPError(str(exc)) from exc
            return status, content_type, bounded_body, chain
        raise SafeHTTPError("redirect limit exceeded")
