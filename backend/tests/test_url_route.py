from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_url_endpoint_rejects_invalid_url():
    response = client.post("/api/v1/url/analyze", json={"url": "javascript:alert(1)"})

    assert response.status_code == 422


def test_url_endpoint_returns_explicit_fixture_result():
    response = client.post(
        "/api/v1/url/analyze?fixture_mode=true",
        json={"url": "https://example.com/login"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "fixture"
    assert body["status"] == "success"
    assert "fixture" in " ".join(body["limitations"]).lower()


def test_url_endpoint_reports_provider_unavailable_without_configuration(monkeypatch):
    monkeypatch.delenv("GOOGLE_WEB_RISK_API_KEY", raising=False)

    response = client.post("/api/v1/url/analyze", json={"url": "https://example.com"})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "unavailable"
    assert body["mode"] == "unavailable"
