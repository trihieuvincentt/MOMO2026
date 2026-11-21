from fastapi.testclient import TestClient

import backend.app.api.routes.cases as cases_routes
from backend.app.services.case_service import InMemoryCaseRepository
from backend.app.main import app

client = TestClient(app)


def setup_function():
    cases_routes.case_repository = InMemoryCaseRepository()


def test_report_endpoint_returns_structured_report_for_analyzed_case():
    case_id = client.post("/api/v1/cases").json()["id"]
    client.post(
        f"/api/v1/cases/{case_id}/evidence",
        json={"type": "message", "content_reference": "Pay a verification fee"},
    )
    client.post(f"/api/v1/cases/{case_id}/analyze")

    response = client.get(f"/api/v1/cases/{case_id}/report")

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == case_id
    assert "risk" in body
    assert body["evidence_items"]
    assert body["findings"]
    assert body["actions"]


def test_report_endpoint_returns_not_found_for_unknown_case():
    response = client.get("/api/v1/cases/case-unknown/report")

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


def test_report_endpoint_exposes_unavailable_scanner_limitations():
    case_id = client.post("/api/v1/cases").json()["id"]
    client.post(
        f"/api/v1/cases/{case_id}/evidence",
        json={"type": "url", "content_reference": "https://example.com"},
    )
    client.post(f"/api/v1/cases/{case_id}/analyze")

    body = client.get(f"/api/v1/cases/{case_id}/report").json()

    assert body["risk"]["category"] in {"insufficient_information", "no_known_signal_found", "caution", "elevated_risk"}
    assert "limitations" in body
