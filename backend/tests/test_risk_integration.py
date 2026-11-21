from backend.app.schemas.case import EvidenceScanStatus
from backend.app.schemas.evidence import EvidenceType
from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.risk import RiskCategory
from backend.app.services.case_service import (
    InMemoryCaseRepository,
    ScannerRegistry,
    add_evidence,
    analyze_case,
    create_case,
)
from backend.app.schemas.message import MessageScanResult, ScannerStatus


def test_case_analysis_persists_risk_category_policy_version_and_recommendations():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    add_evidence(repository, case.id, EvidenceType.MESSAGE, "Please pay a verification fee")
    finding = Finding(
        id="fee-finding",
        category="advance_fee",
        description="An upfront fee was requested.",
        evidence_item_id=None,
        source_type=FindingSource.RULE,
        verification_status=VerificationStatus.SUSPICIOUS_INDICATOR,
        severity=Severity.HIGH,
    )

    result = analyze_case(
        repository,
        case.id,
        ScannerRegistry(
            message=lambda text: MessageScanResult(
                summary="suspicious",
                findings=[finding],
                limitations=[],
                status=ScannerStatus.SUCCESS,
            )
        ),
    )

    assert result.case.risk_assessment is not None
    assert result.case.risk_assessment.category == RiskCategory.ELEVATED_RISK
    assert result.case.risk_assessment.policy_version == "2026-11-21.v1"
    assert result.case.risk_assessment.contributing_finding_ids == ["fee-finding"]
    assert result.case.risk_assessment.recommendations
    assert result.case.overall_risk == RiskCategory.ELEVATED_RISK


def test_case_analysis_marks_unavailable_checks_as_insufficient_information():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    add_evidence(repository, case.id, EvidenceType.URL, "https://example.com")

    result = analyze_case(
        repository,
        case.id,
        ScannerRegistry(url=lambda value: (_ for _ in ()).throw(TimeoutError("timeout"))),
    )

    assert result.case.risk_assessment.category == RiskCategory.INSUFFICIENT_INFORMATION
    assert result.case.risk_assessment.unknowns
