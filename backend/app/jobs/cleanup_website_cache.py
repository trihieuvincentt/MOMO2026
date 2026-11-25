import logging
import os
from collections.abc import Callable

from backend.app.repositories.website_cache_repository import WebsiteCacheRepository
from backend.app.services.website_analysis_cache import WebsiteAnalysisCache

logger = logging.getLogger(__name__)
CacheFactory = Callable[[str], WebsiteAnalysisCache]


def _default_cache_factory(database_url: str) -> WebsiteAnalysisCache:
    return WebsiteAnalysisCache(WebsiteCacheRepository(database_url))


def run_cleanup(
    database_url: str | None = None,
    *,
    cache_factory: CacheFactory | None = None,
) -> bool:
    configured_url = database_url if database_url is not None else os.getenv("DATABASE_URL", "")
    if not configured_url.strip():
        logger.error("website cache cleanup failed: DATABASE_URL is not configured")
        return False
    try:
        cache = (cache_factory or _default_cache_factory)(configured_url.strip())
        cache.cleanup()
    except Exception:
        logger.error("website cache cleanup failed")
        return False
    logger.info("website cache cleanup completed")
    return True


def main() -> int:
    return 0 if run_cleanup() else 1


if __name__ == "__main__":
    raise SystemExit(main())
