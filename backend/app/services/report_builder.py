from datetime import datetime, timezone

from backend.app.schemas.case import Case, EvidenceScanStatus
from backend.app.schemas.report import (
    InvestigationReport,
    ReportEvidenceItem,
    ReportFinding,
)
from backend.app.schemas.risk import Recommendation, RiskAssessment, RiskCategory


def build_report(
    case: Case,
    risk: RiskAssessment,
    recommendations: list[Recommendation],
) -> InvestigationReport:
    evidence_by_id = {item.id: item for item in case.evidence}
    evidence_items = [
        ReportEvidenceItem(
            id=item.id,
            type=item.type.value,
            content_reference=item.content_reference,
            status=case.scanner_statuses.get(item.id),
        )
        for item in case.evidence
    ]
    report_findings: list[ReportFinding] = []
    limitations: list[str] = []
    for finding in case.findings:
        supported = finding.evidence_item_id in evidence_by_id if finding.evidence_item_id else False
        if not supported:
            limitations.append(f"Finding {finding.id} has no resolvable evidence reference and is not presented as supported.")
        report_findings.append(ReportFinding(finding=finding, supported=supported))

    scanner_statuses = [
        ReportEvidenceItem(
            id=evidence_id,
            type="scanner_status",
            content_reference=None,
            status=status,
        )
        for evidence_id, status in case.scanner_statuses.items()
    ]
    for item in scanner_statuses:
        if item.status in {EvidenceScanStatus.UNAVAILABLE, EvidenceScanStatus.ERROR}:
            limitations.append(f"Scanner check for {item.id} is {item.status.value}.")

    if risk.category == RiskCategory.NO_KNOWN_SIGNAL_FOUND:
        limitations.append("No known signal found is not a guarantee of safety.")
    if not case.evidence:
        limitations.append("The case is empty; there is insufficient information for a meaningful report.")

    ai_summary = case.investigation.summary if case.investigation else None
    if case.investigation:
        limitations.extend(case.investigation.limitations)
        limitations.extend(case.investigation.unknowns)

    return InvestigationReport(
        case_id=case.id,
        generated_at=datetime.now(timezone.utc).isoformat(),
        risk=risk,
        summary=case.summary or risk.explanation,
        ai_summary=ai_summary,
        evidence_items=evidence_items,
        artifacts=case.artifacts,
        campaign_matches=case.campaign_matches,
        findings=report_findings,
        relationships=case.relationships,
        scanner_statuses=scanner_statuses,
        unknowns=risk.unknowns,
        limitations=list(dict.fromkeys(limitations)),
        actions=recommendations or risk.recommendations,
    )
