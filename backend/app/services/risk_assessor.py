from collections.abc import Iterable

from backend.app.schemas.case import EvidenceScanStatus
from backend.app.schemas.finding import Finding, Severity, VerificationStatus
from backend.app.schemas.risk import RiskAssessment, RiskCategory

POLICY_VERSION = "2026-11-21.v1"


def _unique_findings(findings: Iterable[Finding]) -> tuple[list[Finding], list[str]]:
    unique: list[Finding] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    for finding in findings:
        if finding.id in seen:
            duplicates.append(f"Duplicate finding {finding.id} was counted once.")
            continue
        seen.add(finding.id)
        unique.append(finding)
    return unique, duplicates


def assess_risk(
    findings: list[Finding],
    scanner_statuses: list[EvidenceScanStatus | str],
) -> RiskAssessment:
    unique, unknowns = _unique_findings(findings)
    successful = any(str(status) == EvidenceScanStatus.SUCCESS for status in scanner_statuses)
    unavailable = any(
        str(status) in {EvidenceScanStatus.UNAVAILABLE, EvidenceScanStatus.ERROR}
        for status in scanner_statuses
    )

    by_category: dict[str, set[VerificationStatus]] = {}
    for finding in unique:
        by_category.setdefault(finding.category, set()).add(finding.verification_status)
    for category, statuses in by_category.items():
        if VerificationStatus.VERIFIED_MATCH in statuses and VerificationStatus.NO_SIGNAL_FOUND in statuses:
            unknowns.append(f"Contradictory findings were returned for category {category}.")

    verified = [
        finding for finding in unique
        if finding.verification_status == VerificationStatus.VERIFIED_MATCH
    ]
    suspicious = [
        finding for finding in unique
        if finding.verification_status == VerificationStatus.SUSPICIOUS_INDICATOR
    ]
    unverified = [
        finding for finding in unique
        if finding.verification_status == VerificationStatus.UNVERIFIED
    ]

    if verified:
        category = RiskCategory.HIGH_RISK
        reason = f"Verified reputation or evidence matches support high risk: {', '.join(f.id for f in verified)}."
        contributing = [finding.id for finding in verified]
    elif unverified or unavailable or not successful:
        category = RiskCategory.INSUFFICIENT_INFORMATION
        reason = "The assessment is limited because one or more checks were not verified or unavailable."
        contributing = [finding.id for finding in unverified]
        if unavailable:
            unknowns.append("One or more scanner checks were unavailable or failed.")
    elif any(finding.severity == Severity.HIGH for finding in suspicious):
        category = RiskCategory.ELEVATED_RISK
        contributing = [finding.id for finding in suspicious if finding.severity == Severity.HIGH]
        reason = f"Strong suspicious indicators require caution: {', '.join(contributing)}."
    elif len(suspicious) >= 2:
        category = RiskCategory.ELEVATED_RISK
        contributing = [finding.id for finding in suspicious]
        reason = f"Multiple suspicious indicators were found: {', '.join(contributing)}."
    elif suspicious:
        category = RiskCategory.CAUTION
        contributing = [finding.id for finding in suspicious]
        reason = f"A weaker suspicious indicator was found: {contributing[0]}."
    else:
        category = RiskCategory.NO_KNOWN_SIGNAL_FOUND
        contributing = []
        reason = "The completed checks found no known signal; this is not a guarantee of safety."
        unknowns.append("Reputation and rule-based checks cannot detect every scam.")

    return RiskAssessment(
        category=category,
        explanation=reason,
        contributing_finding_ids=contributing,
        unknowns=unknowns,
        policy_version=POLICY_VERSION,
    )
