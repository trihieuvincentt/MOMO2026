from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_evidence_fusion_route_returns_explainable_result():
    response = client.post(
        "/api/v1/evidence/fuse",
        json={
            "visual": {
                "status": "success",
                "site_type": "banking",
                "indicators": [{"category": "brand_impersonation", "description": "Imitated bank", "confidence": 0.9}],
                "sensitive_data_requested": ["password", "otp"],
            },
            "links": {
                "links": [{"url": "https://fake.example/login", "domain": "fake.example", "relationship": "external", "role": "login", "indicators": ["brand_domain_mismatch"], "severity": "high"}],
                "deep_analysis_targets": [],
                "limitations": [],
            },
            "reputation_matches": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["category"] == "high_risk"
    assert payload["reasons"]
    assert all(reason["evidence_source"] for reason in payload["reasons"])


def test_evidence_fusion_route_handles_empty_evidence():
    response = client.post("/api/v1/evidence/fuse", json={})

    assert response.status_code == 200
    assert response.json()["category"] == "insufficient_information"
