import base64
import json
import urllib.request
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode


@dataclass(frozen=True)
class ReputationLookup:
    matched: bool
    source: str
    details: str | None = None
    sources: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()


class ReputationProviderUnavailable(TimeoutError):
    """The reputation provider cannot currently answer the lookup."""


class ReputationProvider(Protocol):
    def lookup(self, url: str) -> ReputationLookup:
        """Look up a validated URL without fetching its page."""


Transport = Callable[[str, str, dict[str, str], bytes | None, float], tuple[int, bytes]]


def _http_transport(
    method: str,
    request_url: str,
    headers: dict[str, str],
    body: bytes | None,
    timeout: float,
) -> tuple[int, bytes]:
    request = urllib.request.Request(request_url, headers=headers, method=method, data=body)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return int(response.status), response.read()
    except HTTPError as exc:
        return exc.code, exc.read()
    except URLError as exc:
        raise ReputationProviderUnavailable("Reputation provider network failure") from exc


def _parse_json(body: bytes, provider_name: str) -> dict[str, Any]:
    try:
        payload = json.loads(body)
    except (TypeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{provider_name} returned malformed JSON") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"{provider_name} returned an invalid response")
    return payload


def _handle_http_status(status: int, provider_name: str) -> None:
    if status == 429 or status >= 500:
        raise ReputationProviderUnavailable(f"{provider_name} returned HTTP {status}")
    if status >= 400:
        raise RuntimeError(f"{provider_name} returned HTTP {status}")


class VirusTotalProvider:
    """VirusTotal URL lookup using its multi-engine analysis statistics."""

    endpoint = "https://www.virustotal.com/api/v3/urls"
    source = "virustotal"

    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 5.0,
        transport: Transport = _http_transport,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("VirusTotal API key is required")
        self._api_key = api_key.strip()
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def lookup(self, url: str) -> ReputationLookup:
        url_id = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
        status, body = self._transport(
            "GET",
            f"{self.endpoint}/{url_id}",
            {"Accept": "application/json", "x-apikey": self._api_key},
            None,
            self._timeout_seconds,
        )
        if status == 404:
            return ReputationLookup(
                matched=False,
                source=self.source,
                details="No VirusTotal analysis record was found.",
            )
        _handle_http_status(status, "VirusTotal")
        payload = _parse_json(body, "VirusTotal")
        stats = payload.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        malicious = int(stats.get("malicious", 0) or 0)
        suspicious = int(stats.get("suspicious", 0) or 0)
        if malicious or suspicious:
            return ReputationLookup(
                matched=True,
                source=self.source,
                details=f"VirusTotal multi-engine analysis reported {malicious} malicious and {suspicious} suspicious engines.",
            )
        return ReputationLookup(
            matched=False,
            source=self.source,
            details="VirusTotal reported no malicious or suspicious engine detections.",
        )


class URLhausProvider:
    """URLhaus malware URL lookup; it does not download the submitted URL."""

    endpoint = "https://urlhaus-api.abuse.ch/v1/url/"
    source = "urlhaus"

    def __init__(
        self,
        api_key: str,
        *,
        timeout_seconds: float = 5.0,
        transport: Transport = _http_transport,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("URLhaus API key is required")
        self._api_key = api_key.strip()
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def lookup(self, url: str) -> ReputationLookup:
        body = urlencode({"url": url}).encode()
        status, response_body = self._transport(
            "POST",
            self.endpoint,
            {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
                "Auth-Key": self._api_key,
            },
            body,
            self._timeout_seconds,
        )
        _handle_http_status(status, "URLhaus")
        payload = _parse_json(response_body, "URLhaus")
        if payload.get("query_status") == "no_results":
            return ReputationLookup(
                matched=False,
                source=self.source,
                details="URLhaus found no malware URL record.",
            )
        if payload.get("query_status") != "ok":
            raise RuntimeError("URLhaus returned an indeterminate query status")

        threat = payload.get("threat") or "malware URL"
        url_status = payload.get("url_status") or "unknown status"
        tags = payload.get("tags") or []
        tag_text = f" Tags: {', '.join(str(tag) for tag in tags)}." if tags else ""
        return ReputationLookup(
            matched=True,
            source=self.source,
            details=f"URLhaus reported {threat} ({url_status}).{tag_text}",
        )


class MultiSourceReputationProvider:
    """Combine independent reputation sources without hiding partial failures."""

    def __init__(self, providers: Iterable[ReputationProvider]) -> None:
        self._providers = tuple(providers)

    def lookup(self, url: str) -> ReputationLookup:
        results: list[ReputationLookup] = []
        failures: list[tuple[str, Exception]] = []
        for provider in self._providers:
            name = provider.__class__.__name__.removesuffix("Provider")
            try:
                results.append(provider.lookup(url))
            except Exception as exc:
                failures.append((name, exc))

        if not results:
            if any(isinstance(error, ReputationProviderUnavailable) for _, error in failures):
                raise ReputationProviderUnavailable("All reputation providers were unavailable")
            raise RuntimeError("All reputation providers failed")

        sources = tuple(result.source for result in results)
        details = " ".join(result.details or "" for result in results).strip()
        limitations = tuple(
            f"{name} lookup failed; this result is partial."
            for name, _ in failures
        )
        return ReputationLookup(
            matched=any(result.matched for result in results),
            source="+".join(sources),
            details=details,
            sources=sources,
            limitations=limitations,
        )
