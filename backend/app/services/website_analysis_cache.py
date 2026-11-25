from datetime import datetime, timedelta, timezone

from backend.app.repositories.website_cache_repository import CachedWebsite, WebsiteCacheRepository


class WebsiteAnalysisCache:
    def __init__(self, repository: WebsiteCacheRepository, *, ttl_hours: int = 24) -> None:
        self.repository = repository
        self.ttl = timedelta(hours=ttl_hours)

    def get(self, url: str, *, force_reanalysis: bool = False) -> CachedWebsite | None:
        if force_reanalysis:
            return None
        return self.repository.get(url)

    def put(self, url: str, payload: dict) -> CachedWebsite:
        return self.repository.save(
            url,
            payload,
            expires_at=datetime.now(timezone.utc) + self.ttl,
        )

    def cleanup(self) -> None:
        self.repository.cleanup_expired()
