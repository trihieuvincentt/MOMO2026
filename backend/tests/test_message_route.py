from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_message_analyze_endpoint_returns_structured_result():
    response = client.post(
        "/api/v1/message/analyze",
        json={"text": "Pay a verification fee before your job offer."},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["findings"][0]["evidence_excerpt"] in "Pay a verification fee before your job offer."


def test_message_analyze_endpoint_rejects_blank_text():
    response = client.post("/api/v1/message/analyze", json={"text": " "})
    assert response.status_code == 422
