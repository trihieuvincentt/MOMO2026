import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from backend.app.config import get_reputation_provider
from backend.app.adapters.gemini_visual import GeminiVisualAnalyzer
from backend.app.repositories.website_cache_repository import WebsiteCacheRepository, normalize_cache_url
from backend.app.repositories.website_graph_repository import WebsiteGraphRepository
from backend.app.services.browser_snapshot import BrowserSnapshotError, BrowserSnapshotService
from backend.app.services.website_analysis_cache import WebsiteAnalysisCache
from backend.app.services.website_investigation import WebsiteInvestigationService
from backend.app.services.visual_analysis import VisualAnalysisService
from backend.app.services.request_limits import (
    AnalysisConcurrencyGate,
    RateLimitExceeded,
    SlidingWindowRateLimiter,
)

router = APIRouter(prefix="/api/v1/websites", tags=["websites"])
website_rate_limiter = SlidingWindowRateLimiter(max_requests=20, window_seconds=60)
website_concurrency_gate = AnalysisConcurrencyGate(max_concurrent=2, wait_seconds=0.25)


class WebsiteAnalysisRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    force_reanalysis: bool = False
    claimed_brands: list[str] = Field(default_factory=list, max_length=20)


class InMemoryWebsiteCache:
    def __init__(self, *, ttl_hours: int = 24):
        self._payloads = {}
        self._ttl = timedelta(hours=ttl_hours)

    def get(self, url: str, *, force_reanalysis: bool = False, now: datetime | None = None):
        if force_reanalysis:
            return None
        normalized = normalize_cache_url(url)
        cached = self._payloads.get(normalized)
        if cached is None:
            return None
        current = now or datetime.now(timezone.utc)
        if cached["expires_at"] <= current:
            self._payloads.pop(normalized, None)
            return None
        return type("CachedWebsite", (), {"payload": cached["payload"], "expires_at": cached["expires_at"]})()

    def put(self, url: str, payload: dict):
        normalized = normalize_cache_url(url)
        expires_at = datetime.now(timezone.utc) + self._ttl
        self._payloads[normalized] = {"payload": payload, "expires_at": expires_at}
        return payload

    def cleanup(self, *, now: datetime | None = None):
        current = now or datetime.now(timezone.utc)
        for url, cached in list(self._payloads.items()):
            if cached["expires_at"] <= current:
                self._payloads.pop(url, None)


_memory_cache = InMemoryWebsiteCache()


def get_website_investigation_service() -> WebsiteInvestigationService:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        cache = WebsiteAnalysisCache(WebsiteCacheRepository(database_url))
        graph_repository = WebsiteGraphRepository(database_url)
    else:
        cache = _memory_cache
        graph_repository = None
    visual_analyzer = None
    enabled = os.getenv("GEMINI_ENABLED", "false").strip().lower() in {"1", "true", "yes", "on"}
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if enabled and api_key:
        visual_analyzer = GeminiVisualAnalyzer(
            api_key,
            model_name=os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash",
        )
    return WebsiteInvestigationService(
        snapshot_service=BrowserSnapshotService(),
        cache=cache,
        visual_service=VisualAnalysisService(visual_analyzer),
        reputation_provider=get_reputation_provider(),
        graph_repository=graph_repository,
    )


@router.post("/analyze")
async def analyze_website(request: WebsiteAnalysisRequest, http_request: Request) -> dict:
    peer_key = http_request.client.host if http_request.client else "unknown"
    try:
        website_rate_limiter.check(peer_key)
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="Website analysis rate limit exceeded",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    service = get_website_investigation_service()
    try:
        return await run_in_threadpool(
            website_concurrency_gate.run,
            service.analyze,
            request.url,
            force_reanalysis=request.force_reanalysis,
            claimed_brands=request.claimed_brands,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="Website analysis capacity is busy; retry shortly",
            headers={"Retry-After": str(exc.retry_after_seconds)},
        ) from exc
    except BrowserSnapshotError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
