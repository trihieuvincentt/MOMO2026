import json
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.parse import urlencode


@dataclass(frozen=True)
class ReputationLookup:
    matched: bool
    source: str
    details: str | None = None


class ReputationProviderUnavailable(TimeoutError):
    """The reputation provider cannot currently answer the lookup."""


class ReputationProvider(Protocol):
    def lookup(self, url: str) -> ReputationLookup:
        """Look up a validated URL without fetching its page."""


Transport = Callable[[str, float], tuple[int, bytes]]


def _http_transport(request_url: str, timeout: float) -> tuple[int, bytes]:
    request = urllib.request.Request(
        request_url,
        headers={"Accept": "application/json", "User-Agent": "ScamGuard/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
        return int(response.status), response.read()


class GoogleWebRiskProvider:
    """Google Web Risk URI lookup; it never downloads the submitted URI."""

    endpoint = "https://webrisk.googleapis.com/v1/uris:search"
    source = "google_web_risk"

    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 3.0,
        transport: Transport = _http_transport,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("Google Web Risk API key is required")
        self._api_key = api_key.strip()
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def lookup(self, url: str) -> ReputationLookup:
        query = urlencode(
            [
                ("key", self._api_key),
                ("uri", url),
                ("threatTypes", "MALWARE"),
                ("threatTypes", "SOCIAL_ENGINEERING"),
                ("threatTypes", "UNWANTED_SOFTWARE"),
            ]
        )
        status, body = self._transport(f"{self.endpoint}?{query}", self._timeout_seconds)
        if status == 429 or status >= 500:
            raise ReputationProviderUnavailable(f"Google Web Risk returned HTTP {status}")
        if status >= 400:
            raise RuntimeError(f"Google Web Risk returned HTTP {status}")
        try:
            payload: dict[str, Any] = json.loads(body)
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Google Web Risk returned malformed JSON") from exc

        threat_types = payload.get("threat", {}).get("threatTypes", [])
        if threat_types:
            rendered = ", ".join(str(value) for value in threat_types)
            return ReputationLookup(
                matched=True,
                source=self.source,
                details=f"Google Web Risk reported: {rendered}.",
            )
        return ReputationLookup(matched=False, source=self.source)
