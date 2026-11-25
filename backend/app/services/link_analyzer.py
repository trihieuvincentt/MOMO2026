from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit

from backend.app.adapters.reputation import ReputationLookup, ReputationProvider
from backend.app.services.content_extractor import ExtractedLink, WebsiteContent


@dataclass(frozen=True)
class AnalyzedLink:
    text: str
    url: str
    domain: str
    relationship: str

    @property
    def is_internal(self) -> bool:
        return self.relationship == "internal"
    role: str | None
    indicators: tuple[str, ...] = ()
    severity: str = "low"
    requires_deep_analysis: bool = False
    reputation_source: str | None = None
    reputation_matched: bool | None = None
    reputation_details: str | None = None


@dataclass(frozen=True)
class LinkAnalysisResult:
    links: list[AnalyzedLink]
    deep_analysis_targets: list[str]
    limitations: list[str] = field(default_factory=list)


def _normalize_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "/", parts.query, ""))


def _site_domain(hostname: str) -> str:
    labels = hostname.casefold().strip(".").split(".")
    return ".".join(labels[-2:]) if len(labels) >= 2 else hostname.casefold()


def _brand_tokens(brands: list[str]) -> set[str]:
    return {brand.casefold().replace(" ", "") for brand in brands}


def _has_brand_mismatch(domain: str, brands: set[str]) -> bool:
    domain_token = domain.split(".", 1)[0].casefold().replace("-", "")
    official_domains = {"facebook.com", "meta.com", "instagram.com", "google.com", "amazon.com", "paypal.com"}
    return bool(brands) and any(brand in domain_token or domain_token in brand for brand in brands) and _site_domain(domain) not in official_domains


def _coerce_lookup(value: ReputationLookup | dict) -> ReputationLookup:
    if isinstance(value, ReputationLookup):
        return value
    return ReputationLookup(
        matched=bool(value.get("matched")),
        source=str(value.get("source", "unknown")),
        details=value.get("details"),
        sources=tuple(value.get("sources", ())),
        limitations=tuple(value.get("limitations", ())),
    )


def analyze_links(
    content: WebsiteContent,
    *,
    source_url: str,
    claimed_brands: list[str] | None = None,
    reputation_provider: ReputationProvider | None = None,
    max_external_targets: int = 5,
) -> LinkAnalysisResult:
    source_domain = _site_domain((urlsplit(source_url).hostname or "").casefold())
    brands = _brand_tokens(claimed_brands or [])
    unique: dict[str, ExtractedLink] = {}
    for link in content.links:
        unique.setdefault(_normalize_url(link.url), link)

    external_count = sum(
        1 for link in unique.values()
        if _site_domain((urlsplit(link.url).hostname or "").casefold()) != source_domain
    )
    limitations: list[str] = []
    if external_count > max_external_targets:
        limitations.append("External target limit exceeded; only the bounded target set was checked.")

    source_brand_mismatch = _has_brand_mismatch(source_domain, brands)
    analyzed: list[AnalyzedLink] = []
    deep_targets: list[str] = []
    checked = 0
    for url, link in unique.items():
        domain = (urlsplit(url).hostname or "").casefold()
        site_domain = _site_domain(domain)
        is_internal = site_domain == source_domain
        indicators: list[str] = []
        requires_deep = False
        severity = "low"
        if (is_internal and source_brand_mismatch) or (
            not is_internal and brands and link.role in {"login", "registration", "verification", "payment"} and not any(
                brand in site_domain.split(".", 1)[0].replace("-", "") for brand in brands
            )
        ):
            indicators.append("brand_domain_mismatch")
            severity = "high"
            requires_deep = True
        if not is_internal:
            indicators.append("external_link")
            if link.role in {"login", "registration", "verification", "payment"}:
                requires_deep = True
            if requires_deep and checked < max_external_targets:
                checked += 1
                deep_targets.append(url)
        lookup: ReputationLookup | None = None
        if not is_internal and checked <= max_external_targets and reputation_provider is not None and url in deep_targets:
            try:
                lookup = _coerce_lookup(reputation_provider.lookup(url))
                if lookup.matched:
                    indicators.append("reputation_match")
                    severity = "high"
            except Exception:
                limitations.append(f"Reputation lookup failed for {domain}.")
        analyzed.append(AnalyzedLink(
            text=link.text,
            url=url,
            domain=domain,
            relationship="internal" if is_internal else "external",
            role=link.role,
            indicators=tuple(indicators),
            severity=severity,
            requires_deep_analysis=requires_deep,
            reputation_source=lookup.source if lookup else None,
            reputation_matched=lookup.matched if lookup else None,
            reputation_details=lookup.details if lookup else None,
        ))
    return LinkAnalysisResult(analyzed, deep_targets, limitations)
