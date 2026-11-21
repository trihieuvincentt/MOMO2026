import re
from uuid import uuid4

from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.message import MessageScanRequest, MessageScanResult, ScannerStatus


_ADVANCE_FEE = re.compile(r".{0,80}(?:verification fee|upfront fee|pay .* before|fee .* before).{0,100}", re.I)
_CREDENTIAL = re.compile(r".{0,80}(?:otp|one[- ]time password|password|recovery code).{0,100}", re.I)


def _finding(category: str, description: str, excerpt: str, severity: Severity) -> Finding:
    return Finding(
        id=f"finding-{uuid4().hex[:10]}",
        category=category,
        description=description,
        evidence_excerpt=excerpt.strip(),
        source_type=FindingSource.RULE,
        verification_status=VerificationStatus.SUSPICIOUS_INDICATOR,
        severity=severity,
    )


def analyze_message(request: MessageScanRequest) -> MessageScanResult:
    findings: list[Finding] = []
    for pattern, category, description, severity in (
        (_ADVANCE_FEE, "advance_fee", "The message appears to request an upfront or verification fee.", Severity.HIGH),
        (_CREDENTIAL, "credential_request", "The message appears to request a password, OTP, or recovery code.", Severity.HIGH),
    ):
        match = pattern.search(request.text)
        if match:
            findings.append(_finding(category, description, match.group(0), severity))

    return MessageScanResult(
        summary=("Suspicious indicators were found." if findings else "No known message indicator was found."),
        findings=findings,
        limitations=["Rule-based baseline; absence of a finding is not a safety guarantee."],
        status=ScannerStatus.SUCCESS,
    )
