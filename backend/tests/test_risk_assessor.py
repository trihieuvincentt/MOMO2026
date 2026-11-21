import pytest

from backend.app.schemas.case import EvidenceScanStatus
from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.risk import RiskCategory
from backend.app.services.risk_assessor import assess_risk


def finding(
    finding_id: str,
    *,
    category: str = "signal",
    verification: VerificationStatus = VerificationStatus.SUSPICIOUS_INDICATOR,
    severity: Severity = Severity.MEDIUM,
) -> Finding:
    return Finding(
        id=finding_id,
        category=category,
        description=f"Description for {finding_id}",
        evidence_item_id="evidence-1",
        source_type=FindingSource.RULE,
        verification_status=verification,
        severity=severity,
    )


@pytest.mark.parametrize(
    ("findings", "statuses", "category"),
    [
        ([finding("malware", verification=VerificationStatus.VERIFIED_MATCH, severity=Severity.HIGH)], [EvidenceScanStatus.SUCCESS], RiskCategory.HIGH_RISK),
        ([finding("credential", category="credential_request", severity=Severity.HIGH)], [EvidenceScanStatus.SUCCESS], RiskCategory.ELEVATED_RISK),
        ([finding("urgency", severity=Severity.LOW)], [EvidenceScanStatus.SUCCESS], RiskCategory.CAUTION),
        ([], [EvidenceScanStatus.SUCCESS], RiskCategory.NO_KNOWN_SIGNAL_FOUND),
        ([], [EvidenceScanStatus.UNAVAILABLE], RiskCategory.INSUFFICIENT_INFORMATION),
    ],
)
def test_risk_categories_are_deterministic(findings, statuses, category):
    result = assess_risk(findings, statuses)

    assert result.category == category
    assert result.policy_version == "2026-11-21.v1"
    assert result.explanation


def test_verified_match_references_exact_finding_id():
    result = assess_risk(
        [finding("vt-match", verification=VerificationStatus.VERIFIED_MATCH, severity=Severity.HIGH)],
        [EvidenceScanStatus.SUCCESS],
    )

    assert result.category == RiskCategory.HIGH_RISK
    assert result.contributing_finding_ids == ["vt-match"]
    assert "vt-match" in result.explanation


def test_duplicate_findings_are_not_double_counted():
    duplicate = finding("same", severity=Severity.MEDIUM)

    result = assess_risk([duplicate, duplicate.model_copy()], [EvidenceScanStatus.SUCCESS])

    assert result.contributing_finding_ids == ["same"]
    assert "duplicate" in " ".join(result.unknowns).lower()


def test_contradictory_signals_are_exposed_as_unknown():
    result = assess_risk(
        [
            finding("reputation", category="reputation_lookup", verification=VerificationStatus.VERIFIED_MATCH, severity=Severity.HIGH),
            finding("reputation-clear", category="reputation_lookup", verification=VerificationStatus.NO_SIGNAL_FOUND, severity=Severity.LOW),
        ],
        [EvidenceScanStatus.SUCCESS],
    )

    assert result.category == RiskCategory.HIGH_RISK
    assert any("contradict" in unknown.lower() for unknown in result.unknowns)
