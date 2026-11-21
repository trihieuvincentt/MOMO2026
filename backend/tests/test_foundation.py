from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.case import Case
from backend.app.schemas.evidence import EvidenceItem
from backend.app.schemas.finding import Finding

client = TestClient(app)


def test_health_endpoint_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_shared_contracts_reject_invalid_enums():
    evidence = EvidenceItem(id="e-1", type="message", content_reference="case text")
    finding = Finding(
        id="f-1",
        category="advance_fee",
        description="Upfront fee requested",
        evidence_item_id=evidence.id,
        evidence_excerpt="pay fee",
        source_type="rule",
        verification_status="suspicious_indicator",
        severity="high",
    )
    case = Case(id="case-1", evidence=[evidence], findings=[finding])
    assert case.findings[0].evidence_item_id == "e-1"

    try:
        Finding(
            id="f-2",
            category="unknown",
            description="bad",
            source_type="rule",
            verification_status="not-a-status",
            severity="high",
        )
    except ValueError:
        pass
    else:
        raise AssertionError("invalid verification status must be rejected")
