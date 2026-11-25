from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.app.api.routes import websites
from backend.app.main import app


client = TestClient(app)


def test_website_analyze_route_returns_pipeline_result(monkeypatch):
    monkeypatch.setattr(
        websites,
        "get_website_investigation_service",
        lambda: SimpleNamespace(analyze=lambda url, **kwargs: {"cache_hit": False, "fusion": {"category": "caution"}}),
    )

    response = client.post("/api/v1/websites/analyze", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json()["fusion"]["category"] == "caution"


def test_website_analyze_route_validates_url_length():
    response = client.post("/api/v1/websites/analyze", json={"url": "x" * 2049})

    assert response.status_code == 422


def test_website_route_passes_force_reanalysis_and_brand_context(monkeypatch):
    seen = {}

    def analyze(url, **kwargs):
        seen.update(kwargs)
        return {"cache_hit": False, "fusion": {"category": "caution"}}

    monkeypatch.setattr(websites, "get_website_investigation_service", lambda: SimpleNamespace(analyze=analyze))
    response = client.post(
        "/api/v1/websites/analyze",
        json={"url": "https://example.com", "force_reanalysis": True, "claimed_brands": ["Example"]},
    )

    assert response.status_code == 200
    assert seen["force_reanalysis"] is True
    assert seen["claimed_brands"] == ["Example"]


def test_website_service_enables_gemini_visual_when_configured(monkeypatch):
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-test")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(websites, "get_reputation_provider", lambda: None)

    service = websites.get_website_investigation_service()

    assert service.visual_service.analyzer is not None
    assert service.visual_service.analyzer.model_name == "gemini-test"


def test_memory_cache_expires_entries_and_normalizes_keys():
    cache = websites.InMemoryWebsiteCache(ttl_hours=1)
    cache.put("https://EXAMPLE.com#frag", {"risk": "low"})

    cached = cache.get("https://example.com/")
    expired = cache.get("https://example.com/", now=datetime.now(timezone.utc) + timedelta(hours=2))

    assert cached is not None
    assert cached.payload["risk"] == "low"
    assert expired is None
