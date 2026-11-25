from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from backend.app.services.browser_snapshot import BrowserSnapshot
from backend.app.services.content_extractor import extract_website_content
from backend.app.services.evidence_fusion import EvidenceFusionService
from backend.app.services.website_investigation import WebsiteInvestigationService
from backend.app.services.website_analysis_cache import WebsiteAnalysisCache


class FakeSnapshotService:
    def __init__(self):
        self.calls = 0

    def capture(self, url):
        self.calls += 1
        return BrowserSnapshot(
            requested_url=url,
            normalized_url="https://example.com/",
            final_url="https://example.com/",
            status_code=200,
            title="Example",
            screenshot_bytes=b"PNG",
            html='<html><title>Example</title><a href="/login">Login</a></html>',
            redirect_chain=("https://example.com/",),
        )


class FakeCache:
    def __init__(self):
        self.payload = None
        self.put_calls = 0

    def get(self, url, *, force_reanalysis=False):
        return None if force_reanalysis or self.payload is None else type("Cached", (), {"payload": self.payload})()

    def put(self, url, payload):
        self.put_calls += 1
        self.payload = payload
        return payload


def test_website_workflow_runs_pipeline_and_caches_result():
    snapshot = FakeSnapshotService()
    cache = FakeCache()
    service = WebsiteInvestigationService(snapshot_service=snapshot, cache=cache, visual_service=None)

    result = service.analyze("https://example.com")

    assert result["cache_hit"] is False
    assert result["snapshot"]["title"] == "Example"
    assert result["content"]["title"] == "Example"
    assert result["fusion"]["category"] == "no_known_signal_found"
    assert snapshot.calls == 1
    assert cache.put_calls == 1
    assert "visible_text" not in result["content"]


def test_website_workflow_reuses_cached_result():
    snapshot = FakeSnapshotService()
    cache = FakeCache()
    first = WebsiteInvestigationService(snapshot_service=snapshot, cache=cache, visual_service=None)
    first.analyze("https://example.com")

    second = WebsiteInvestigationService(snapshot_service=snapshot, cache=cache, visual_service=None)
    result = second.analyze("https://example.com")

    assert result["cache_hit"] is True
    assert snapshot.calls == 1


def test_force_reanalysis_bypasses_cache():
    snapshot = FakeSnapshotService()
    cache = FakeCache()
    service = WebsiteInvestigationService(snapshot_service=snapshot, cache=cache, visual_service=None)
    service.analyze("https://example.com")
    result = service.analyze("https://example.com", force_reanalysis=True)

    assert result["cache_hit"] is False
    assert snapshot.calls == 2


def test_different_claimed_brands_do_not_reuse_context_sensitive_cache():
    snapshot = FakeSnapshotService()
    cache = FakeCache()
    service = WebsiteInvestigationService(snapshot_service=snapshot, cache=cache, visual_service=None)
    service.analyze("https://example.com", claimed_brands=["Brand A"])
    result = service.analyze("https://example.com", claimed_brands=["Brand B"])

    assert result["cache_hit"] is False
    assert snapshot.calls == 2


def test_visual_analysis_is_invoked_with_extracted_context():
    snapshot = FakeSnapshotService()

    class Visual:
        def __init__(self):
            self.calls = 0

        def analyze(self, snapshot, *, claimed_brands, deterministic_context):
            self.calls += 1
            assert claimed_brands == ["Example"]
            assert "Sensitive fields" in deterministic_context
            return SimpleNamespace(
                status="success", site_type="banking", detected_brands=["Example"],
                forms=[], indicators=[], sensitive_data_requested=[], limitations=[],
                screenshot_url=None, model_name="gemini-test",
            )

    visual = Visual()
    service = WebsiteInvestigationService(snapshot_service=snapshot, cache=FakeCache(), visual_service=visual)
    result = service.analyze("https://example.com", claimed_brands=["Example"])

    assert visual.calls == 1
    assert result["visual"]["model_name"] == "gemini-test"


def test_graph_repository_persists_website_links_and_analysis():
    snapshot = FakeSnapshotService()

    class Graph:
        def __init__(self):
            self.websites = []
            self.links = []
            self.analyses = []

        def save_website(self, url, payload, *, expires_at):
            self.websites.append((url, expires_at))

        def save_link(self, url, payload):
            self.links.append(payload)

        def save_analysis(self, url, payload):
            self.analyses.append(payload)

    graph = Graph()
    service = WebsiteInvestigationService(snapshot_service=snapshot, cache=FakeCache(), graph_repository=graph)
    service.analyze("https://example.com")

    assert graph.websites
    assert graph.links
    assert graph.analyses
    assert graph.websites[0][1] is not None
