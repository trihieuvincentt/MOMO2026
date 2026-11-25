from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_link_analysis_route_returns_relationships():
    response = client.post(
        "/api/v1/links/analyze",
        json={
            "source_url": "https://example.com",
            "links": [
                {
                    "text": "Login",
                    "url": "https://login.example.com/login",
                    "domain": "login.example.com",
                    "rel": [],
                    "target": None,
                    "is_internal": True,
                    "role": "login",
                }
            ],
        },
    )

    assert response.status_code == 200
    assert response.json()["links"][0]["relationship"] == "internal"


def test_link_analysis_route_rejects_blank_source_url():
    response = client.post("/api/v1/links/analyze", json={"source_url": "", "links": []})

    assert response.status_code == 422
