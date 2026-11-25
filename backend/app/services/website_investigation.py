from dataclasses import asdict, is_dataclass
from datetime import datetime, timedelta, timezone

from backend.app.services.content_extractor import extract_website_content
from backend.app.services.evidence_fusion import EvidenceFusionService
from backend.app.services.link_analyzer import analyze_links


class WebsiteInvestigationService:
    def __init__(self, *, snapshot_service, cache, visual_service=None, reputation_provider=None, graph_repository=None):
        self.snapshot_service = snapshot_service
        self.cache = cache
        self.visual_service = visual_service
        self.reputation_provider = reputation_provider
        self.graph_repository = graph_repository

    def analyze(self, url: str, *, force_reanalysis: bool = False, claimed_brands: list[str] | None = None) -> dict:
        brands = sorted({brand.strip() for brand in (claimed_brands or []) if brand.strip()})
        cached = self.cache.get(url, force_reanalysis=force_reanalysis)
        if cached is not None:
            payload = cached.payload
            cached_brands = payload.get("analysis_context", {}).get("claimed_brands", [])
            if cached_brands == brands:
                return {**payload, "cache_hit": True}

        snapshot = self.snapshot_service.capture(url)
        content = extract_website_content(snapshot.html, base_url=snapshot.final_url)
        links = analyze_links(
            content,
            source_url=snapshot.final_url,
            claimed_brands=claimed_brands or [],
            reputation_provider=self.reputation_provider,
        )
        visual = None
        if self.visual_service is not None:
            visual = self.visual_service.analyze(
                snapshot,
                claimed_brands=brands,
                deterministic_context=self._deterministic_context(content, links),
            )
        fusion = EvidenceFusionService().fuse(
            visual=visual,
            content=content,
            links=links,
            reputation_matches=sum(1 for item in links.links if item.reputation_matched),
        )
        content_payload = self._serialize(content)
        # Keep extracted metadata for reuse, but do not retain full rendered page text.
        content_payload.pop("visible_text", None)
        payload = {
            "snapshot": {
                "normalized_url": snapshot.normalized_url,
                "final_url": snapshot.final_url,
                "status_code": snapshot.status_code,
                "title": snapshot.title,
                "redirect_chain": list(snapshot.redirect_chain),
            },
            "content": content_payload,
            "links": self._serialize(links),
            "visual": self._serialize(visual),
            "fusion": self._serialize(fusion),
            "analysis_context": {"claimed_brands": brands},
            "cache_hit": False,
        }
        self.cache.put(snapshot.normalized_url, payload)
        if self.graph_repository is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            self.graph_repository.save_website(
                snapshot.normalized_url,
                {"snapshot": payload["snapshot"], "analysis_context": payload["analysis_context"]},
                expires_at=expires_at,
            )
            for link in payload["links"]["links"]:
                self.graph_repository.save_link(snapshot.normalized_url, link)
            self.graph_repository.save_analysis(
                snapshot.normalized_url,
                {"visual": payload["visual"], "content": payload["content"], "links": payload["links"], "fusion": payload["fusion"]},
            )
        return payload

    @staticmethod
    def _deterministic_context(content, links) -> str:
        sensitive = [field.name for form in content.forms for field in form.fields if field.sensitivity == "sensitive"]
        return f"Sensitive fields: {', '.join(sensitive) or 'none'}; external targets: {len(links.deep_analysis_targets)}"

    @classmethod
    def _serialize(cls, value):
        if value is None:
            return None
        if is_dataclass(value):
            return {key: cls._serialize(item) for key, item in asdict(value).items()}
        if isinstance(value, dict):
            return {key: cls._serialize(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cls._serialize(item) for item in value]
        if hasattr(value, "__dict__"):
            return {key: cls._serialize(item) for key, item in vars(value).items()}
        return value
