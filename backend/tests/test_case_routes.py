import pytest
from fastapi.testclient import TestClient

import backend.app.api.routes.cases as cases_routes
from backend.app.services.case_service import InMemoryCaseRepository
from backend.app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_cases(monkeypatch):
    repository = InMemoryCaseRepository()
    monkeypatch.setattr(cases_routes, "case_repository", repository)
    repository.clear()


def test_case_lifecycle_creates_adds_analyzes_and_reads_case():
    created = client.post("/api/v1/cases")
    assert created.status_code == 201
    case_id = created.json()["id"]

    added = client.post(
        f"/api/v1/cases/{case_id}/evidence",
        json={"type": "message", "content_reference": "Please pay a verification fee"},
    )
    assert added.status_code == 201

    analyzed = client.post(f"/api/v1/cases/{case_id}/analyze")
    assert analyzed.status_code == 200
    assert analyzed.json()["status"] == "analyzed"
    assert analyzed.json()["findings"][0]["evidence_item_id"] == added.json()["id"]

    fetched = client.get(f"/api/v1/cases/{case_id}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == case_id


def test_unknown_case_returns_not_found_without_leaking_case_data():
    response = client.get("/api/v1/cases/case-unknown")

    assert response.status_code == 404
    assert response.json()["detail"] == "Case not found"


def test_duplicate_evidence_returns_conflict():
    case_id = client.post("/api/v1/cases").json()["id"]
    payload = {"type": "url", "content_reference": "https://example.com/"}
    assert client.post(f"/api/v1/cases/{case_id}/evidence", json=payload).status_code == 201

    response = client.post(f"/api/v1/cases/{case_id}/evidence", json=payload)

    assert response.status_code == 409


def test_cases_are_isolated_by_opaque_ids():
    first_id = client.post("/api/v1/cases").json()["id"]
    second_id = client.post("/api/v1/cases").json()["id"]
    client.post(
        f"/api/v1/cases/{first_id}/evidence",
        json={"type": "message", "content_reference": "private case text"},
    )

    second = client.get(f"/api/v1/cases/{second_id}")

    assert second.status_code == 200
    assert second.json()["evidence"] == []
