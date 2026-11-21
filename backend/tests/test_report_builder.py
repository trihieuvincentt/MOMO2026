from datetime import datetime, timezone

import pytest

from backend.app.schemas.case import Case, CaseStatus, EvidenceScanStatus, EvidenceRelationship
from backend.app.schemas.evidence import EvidenceItem, EvidenceType
from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.investigation import InvestigationResult, InvestigationStatus
from backend.app.schemas.risk import RiskAssessment, RiskCategory, Recommendation, RecommendationPriority
from backend.app.services.report_builder import build_report


def risk(category: RiskCategory) -> RiskAssessment:
    return RiskAssessment(
        category=category,
        explanation="Assessment explanation.",
        contributing_finding_ids=["finding-1"] if category != RiskCategory.NO_KNOWN_SIGNAL_FOUND else [],
        unknowns=[],
        recommendations=[Recommendation(action="Pause", reason="Evidence requires caution.", priority=RecommendationPriority.HIGH)],
        policy_version="2026-11-21.v1",
    )


def full_case() -> Case:
    return Case(
        id="case-report",
        status=CaseStatus.ANALYZED,
        evidence=[EvidenceItem(id="evidence-1", type=EvidenceType.MESSAGE, content_reference="Please pay a fee")],
        findings=[Finding(
            id="finding-1", category="advance_fee", description="Upfront fee request",
            evidence_item_id="evidence-1", evidence_excerpt="pay a fee", source_type=FindingSource.RULE,
            verification_status=VerificationStatus.SUSPICIOUS_INDICATOR, severity=Severity.HIGH,
        )],
        scanner_statuses={"evidence-1": EvidenceScanStatus.SUCCESS},
        investigation=InvestigationResult(
            status=InvestigationStatus.SUCCESS, summary="AI explanation.",
            finding_explanations=[], relationships=[], unknowns=[], limitations=[],
        ),
    )


def test_report_contains_summary_evidence_findings_statuses_and_actions():
    report = build_report(full_case(), risk(RiskCategory.ELEVATED_RISK), risk(RiskCategory.ELEVATED_RISK).recommendations)

    assert report.case_id == "case-report"
    assert report.risk.category == RiskCategory.ELEVATED_RISK
    assert report.evidence_items[0].id == "evidence-1"
    assert report.findings[0].evidence_item_id == "evidence-1"
    assert report.findings[0].supported is True
    assert report.actions
    assert report.ai_summary == "AI explanation."


def test_report_marks_unavailable_scanner_and_keeps_successful_results():
    case = full_case()
    case.scanner_statuses["evidence-missing"] = EvidenceScanStatus.UNAVAILABLE

    report = build_report(case, risk(RiskCategory.INSUFFICIENT_INFORMATION), [])

    assert any(item.status == EvidenceScanStatus.UNAVAILABLE for item in report.scanner_statuses)
    assert any("unavailable" in item.lower() for item in report.limitations)
    assert report.findings


def test_no_signal_report_has_explicit_safety_disclaimer():
    case = full_case().model_copy(update={"findings": []})

    report = build_report(case, risk(RiskCategory.NO_KNOWN_SIGNAL_FOUND), [])

    assert any("not a guarantee" in item.lower() for item in report.limitations)


def test_finding_without_existing_evidence_is_not_supported():
    case = full_case().model_copy(update={"findings": [full_case().findings[0].model_copy(update={"evidence_item_id": "missing"})]})

    report = build_report(case, risk(RiskCategory.ELEVATED_RISK), [])

    assert report.findings[0].supported is False
    assert any("evidence" in item.lower() for item in report.limitations)


def test_empty_case_report_is_explicitly_incomplete():
    case = Case(id="empty")

    report = build_report(case, risk(RiskCategory.INSUFFICIENT_INFORMATION), [])

    assert report.evidence_items == []
    assert any("empty" in item.lower() or "insufficient" in item.lower() for item in report.limitations)
