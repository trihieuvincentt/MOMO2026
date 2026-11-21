from backend.app.schemas.case import EvidenceScanStatus
from backend.app.schemas.evidence import EvidenceType
from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.investigation import InvestigationStatus
from backend.app.schemas.message import MessageScanResult, ScannerStatus
from backend.app.services.case_service import (
    InMemoryCaseRepository,
    ScannerRegistry,
    add_evidence,
    analyze_case,
    create_case,
)


def test_case_analysis_persists_grounded_gemini_result():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    add_evidence(repository, case.id, EvidenceType.MESSAGE, "Please pay a fee")
    finding = Finding(
        id="finding-fee",
        category="advance_fee",
        description="Upfront fee request",
        source_type=FindingSource.RULE,
        verification_status=VerificationStatus.SUSPICIOUS_INDICATOR,
        severity=Severity.HIGH,
    )

    class MockInvestigationModel:
        def generate(self, prompt: str):
            assert "finding-fee" in prompt
            return {
                "summary": "The message contains an advance-fee signal.",
                "finding_explanations": [{"finding_id": "finding-fee", "explanation": "The request asks for an upfront payment."}],
                "relationships": [],
                "unknowns": [],
            }

    result = analyze_case(
        repository,
        case.id,
        ScannerRegistry(
            message=lambda text: MessageScanResult(summary="ok", findings=[finding], limitations=[], status=ScannerStatus.SUCCESS),
            investigation_model=MockInvestigationModel(),
        ),
    )

    assert result.case.investigation is not None
    assert result.case.investigation.status == InvestigationStatus.SUCCESS
    assert result.case.investigation.finding_explanations[0].finding_id == "finding-fee"


def test_case_analysis_preserves_risk_when_gemini_degrades():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    add_evidence(repository, case.id, EvidenceType.MESSAGE, "Hello")

    class BrokenModel:
        def generate(self, prompt: str):
            raise TimeoutError("timeout")

    result = analyze_case(
        repository,
        case.id,
        ScannerRegistry(
            investigation_model=BrokenModel(),
        ),
    )

    assert result.case.investigation.status == InvestigationStatus.DEGRADED
    assert result.case.risk_assessment is not None
    assert result.case.overall_risk
