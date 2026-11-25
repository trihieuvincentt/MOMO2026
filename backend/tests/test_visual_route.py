from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.app.api.routes import visual
from backend.app.main import app


client = TestClient(app)


def test_visual_route_returns_degraded_result_when_gemini_disabled(monkeypatch):
    snapshot = SimpleNamespace(
        normalized_url="https://example.com/",
        final_url="https://example.com/",
        title="Example",
        screenshot_bytes=b"PNG",
    )
    monkeypatch.setattr(visual.BrowserSnapshotService, "capture", lambda self, url: snapshot)
    monkeypatch.setattr(visual, "get_visual_analyzer", lambda: None)

    response = client.post("/api/v1/visual/analyze", json={"url": "https://example.com"})

    assert response.status_code == 200
    assert response.json()["status"] == "unavailable"
    assert "not configured" in " ".join(response.json()["limitations"]).lower()
