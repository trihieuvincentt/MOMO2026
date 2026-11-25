from datetime import datetime, timedelta, timezone

from backend.app.services.website_analysis_cache import WebsiteAnalysisCache


def test_cache_facade_supports_force_reanalysis():
    class Repository:
        def __init__(self):
            self.payload = None

        def get(self, url):
            return self.payload

        def save(self, url, payload, *, expires_at):
            self.payload = payload
            return payload

        def cleanup_expired(self):
            pass

    repository = Repository()
    cache = WebsiteAnalysisCache(repository, ttl_hours=1)
    cache.put("https://example.com", {"risk": "low"})

    assert cache.get("https://example.com") == {"risk": "low"}
    assert cache.get("https://example.com", force_reanalysis=True) is None
