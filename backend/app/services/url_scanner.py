import ipaddress
from urllib.parse import SplitResult, urlsplit, urlunsplit
from uuid import uuid4

from backend.app.adapters.reputation import ReputationLookup, ReputationProvider
from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.url import (
    URLObservation,
    URLResultMode,
    URLScanResult,
    URLScanStatus,
)

_MAX_URL_LENGTH = 2048
_ALLOWED_SCHEMES = {"http", "https"}


def _normalized_hostname(parts: SplitResult) -> tuple[str, list[str]]:
    hostname = parts.hostname
    if not hostname:
        raise ValueError("URL must include a hostname")
    try:
        normalized = hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise ValueError("URL hostname is invalid") from exc
    notes: list[str] = []
    if normalized != hostname.lower():
        notes.append("Internationalized hostname normalized to punycode.")
    return normalized, notes


def _is_local_or_private(hostname: str) -> bool:
    if hostname == "localhost" or hostname.endswith(".localhost"):
        return True
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return False
    return bool(
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_reserved
        or address.is_unspecified
    )


def _normalized_netloc(parts: SplitResult, hostname: str) -> str:
    try:
        port = parts.port
    except ValueError as exc:
        raise ValueError("URL port is invalid") from exc
    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    return rendered_host if port is None else f"{rendered_host}:{port}"


def parse_submitted_url(raw: str) -> URLObservation:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("URL is required")
    value = raw.strip()
    if len(value) > _MAX_URL_LENGTH:
        raise ValueError("URL length exceeds the allowed limit")

    try:
        parts = urlsplit(value)
    except ValueError as exc:
        raise ValueError("URL is malformed") from exc
    scheme = parts.scheme.lower()
    if scheme not in _ALLOWED_SCHEMES:
        raise ValueError("URL scheme must be http or https")
    if parts.username is not None or parts.password is not None:
        raise ValueError("URL credentials are not allowed")

    hostname, notes = _normalized_hostname(parts)
    normalized_netloc = _normalized_netloc(parts, hostname)
    is_local_or_private = _is_local_or_private(hostname)
    if is_local_or_private:
        notes.append("Local, private, or link-local targets are not queried.")
    if parts.fragment:
        notes.append("URL fragment was removed before reputation lookup.")

    normalized_url = urlunsplit(
        (scheme, normalized_netloc, parts.path or "/", parts.query, "")
    )
    return URLObservation(
        normalized_url=normalized_url,
        hostname=hostname,
        scheme=scheme,
        notes=notes,
        is_local_or_private=is_local_or_private,
    )


def _finding(
    category: str,
    description: str,
    verification_status: VerificationStatus,
    severity: Severity,
) -> Finding:
    return Finding(
        id=f"finding-{uuid4().hex[:10]}",
        category=category,
        description=description,
        source_type=FindingSource.REPUTATION_API,
        verification_status=verification_status,
        severity=severity,
    )


def _coerce_lookup(value: ReputationLookup | dict) -> ReputationLookup:
    if isinstance(value, ReputationLookup):
        return value
    return ReputationLookup(
        matched=bool(value["matched"]),
        source=str(value["source"]),
        details=value.get("details"),
        sources=tuple(value.get("sources", ())),
        limitations=tuple(value.get("limitations", ())),
    )


def scan_url(
    raw: str,
    provider: ReputationProvider | None,
    fixture_mode: bool = False,
) -> URLScanResult:
    observation = parse_submitted_url(raw)
    if observation.is_local_or_private:
        return URLScanResult(
            observation=observation,
            findings=[
                _finding(
                    "private_target",
                    "The submitted URL targets a local, private, or link-local address and was not queried.",
                    VerificationStatus.UNVERIFIED,
                    Severity.MEDIUM,
                )
            ],
            limitations=["Private and local targets are not fetched or sent to reputation providers."],
            status=URLScanStatus.SUCCESS,
            mode=URLResultMode.UNAVAILABLE,
        )

    if fixture_mode:
        return URLScanResult(
            observation=observation,
            findings=[
                _finding(
                    "reputation_lookup",
                    "No known match was found in the demonstration fixture result.",
                    VerificationStatus.NO_SIGNAL_FOUND,
                    Severity.LOW,
                )
            ],
            limitations=["Fixture result only; this is not a live reputation lookup and is not a safety guarantee."],
            status=URLScanStatus.SUCCESS,
            mode=URLResultMode.FIXTURE,
            lookup_source="fixture",
            lookup_sources=["fixture"],
        )

    if provider is None:
        return URLScanResult(
            observation=observation,
            findings=[
                _finding(
                    "reputation_lookup",
                    "A reputation lookup was not available for this URL.",
                    VerificationStatus.UNVERIFIED,
                    Severity.MEDIUM,
                )
            ],
            limitations=["No reputation provider is configured; the URL was not verified."],
            status=URLScanStatus.UNAVAILABLE,
            mode=URLResultMode.UNAVAILABLE,
        )

    try:
        lookup = _coerce_lookup(provider.lookup(observation.normalized_url))
    except TimeoutError:
        return URLScanResult(
            observation=observation,
            findings=[_finding("reputation_lookup", "The reputation provider timed out.", VerificationStatus.UNVERIFIED, Severity.MEDIUM)],
            limitations=["The live reputation provider timed out; no safety conclusion can be made."],
            status=URLScanStatus.UNAVAILABLE,
            mode=URLResultMode.UNAVAILABLE,
        )
    except Exception:
        return URLScanResult(
            observation=observation,
            findings=[_finding("reputation_lookup", "The reputation provider returned an error.", VerificationStatus.UNVERIFIED, Severity.MEDIUM)],
            limitations=["The live reputation provider failed; no safety conclusion can be made."],
            status=URLScanStatus.ERROR,
            mode=URLResultMode.ERROR,
        )

    if lookup.matched:
        description = lookup.details or "The reputation provider reported a known-risk match."
        finding = _finding("reputation_match", description, VerificationStatus.VERIFIED_MATCH, Severity.HIGH)
        limitations = ["This result reflects the queried reputation source and timestamp."]
    else:
        finding = _finding(
            "reputation_lookup",
            lookup.details or "No known match was found in the queried reputation source.",
            VerificationStatus.NO_SIGNAL_FOUND,
            Severity.LOW,
        )
        limitations = ["No known match from the queried source is not a safety guarantee."]

    limitations.extend(lookup.limitations)
    lookup_sources = list(lookup.sources) or [lookup.source]
    return URLScanResult(
        observation=observation,
        findings=[finding],
        limitations=limitations,
        status=URLScanStatus.SUCCESS,
        mode=URLResultMode.LIVE,
        lookup_source=lookup.source,
        lookup_sources=lookup_sources,
    )
