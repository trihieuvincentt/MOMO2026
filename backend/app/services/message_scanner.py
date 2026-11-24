import re
from uuid import uuid4

from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.message import MessageScanRequest, MessageScanResult, ScannerStatus


_ADVANCE_FEE = re.compile(
    r".{0,100}(?:verification fee|upfront fee|activation fee|processing fee|pay .* before|fee .* before|"
    r"ph[ií]\s+k[ií]ch\s*ho[aạ]t|ph[ií]\s+x[aá]c\s*minh|ph[ií]\s*nhận\s*thưởng|"
    r"chuy[eể]n\s*kho[aả]n).{0,140}",
    re.I,
)
_CREDENTIAL = re.compile(
    r".{0,100}(?:otp|one[- ]time password|password|recovery code|m[aậ]t\s*kh[aẩ]u|"
    r"m[aã]\s*x[aá]c\s*th[ựu]c).{0,140}",
    re.I,
)
_ACCOUNT_DEACTIVATION = re.compile(
    r".{0,100}(?:account\s+(?:will\s+be\s+)?(?:deactivated|disabled|suspended|locked)|"
    r"permanent(?:ly)?\s+(?:deactivation|deactivated|lock)|"
    r"t[aà]i\s*kho[aả]n\s+s[eẽ]\s+b[iị]\s+(?:kh[oó]a|v[oô]\s*hi[eệ]u\s*h[oó]a|đ[iì]nh\s*ch[iỉ])).{0,140}",
    re.I,
)
_VERIFICATION_PHISHING = re.compile(
    r".{0,100}(?:verify\s+your\s+account|complete\s+(?:these\s+)?steps\s+for\s+verification|"
    r"confirm\s+your\s+identity|x[aá]c\s*minh\s+t[aà]i\s*kho[aả]n|"
    r"th[eự]c\s*hi[eệ]n\s+(?:c[aá]c\s+)?b[uư][oớ]c\s+x[aá]c\s*minh).{0,140}",
    re.I,
)
_EXTERNAL_LINK = re.compile(
    r".{0,100}(?:https?://|www\.|click|click\s+here|follow\s+the\s+link|"
    r"truy\s*c[aậ]p|nh[aấ]n\s+v[aà]o|b[aấ]m\s+v[aà]o).{0,180}",
    re.I,
)
_INVESTMENT = re.compile(
    r".{0,100}(?:guaranteed\s+(?:profit|return)|profit\s+\d+%|\d+%\s+(?:in|within)\s+\d+\s*(?:hours?|days?)|"
    r"deposit\s+now|risk[- ]free\s+investment|l[oợ]i\s*nhu[aậ]n\s+(?:đ[aả]m\s*b[aả]o|si[eê]u\s*nhanh)|"
    r"đ[aầ]u\s+tư\s+(?:kh[oô]ng\s+r[uủ]i\s*ro|sinh\s*l[oờ]i)).{0,160}",
    re.I,
)
_PRIZE_CLAIM = re.compile(
    r".{0,120}(?:chúc mừng|trúng giải|giải nhất|giải thưởng|may mắn).{0,180}"
    r"(?:xe máy|phiếu quà tặng|tiền mặt|vnđ|website|truy cập ngay|nhận thưởng).{0,120}",
    re.I,
)
_BRAND_IMPERSONATION = re.compile(
    r".{0,100}(?:facebook|m[obi]{1,2}fone|zalo|ngân hàng|bank).{0,160}"
    r"(?:chúc mừng|trúng giải|tài khoản.*(?:khóa|suspended|deactivated)|xác minh|verify|truy cập ngay).{0,120}",
    re.I,
)


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
        (_ACCOUNT_DEACTIVATION, "account_deactivation_threat", "The message threatens account deactivation, suspension, or lockout to pressure the recipient.", Severity.HIGH),
        (_VERIFICATION_PHISHING, "verification_phishing", "The message asks the recipient to verify an account or identity through an unsolicited request.", Severity.HIGH),
        (_EXTERNAL_LINK, "external_link_request", "The message directs the recipient to click, follow, or visit an external link.", Severity.MEDIUM),
        (_INVESTMENT, "investment_scam", "The message promises unusually high or guaranteed investment returns.", Severity.HIGH),
        (_PRIZE_CLAIM, "prize_claim", "The message appears to promise an unexpected prize and direct the recipient to claim it.", Severity.HIGH),
        (_BRAND_IMPERSONATION, "brand_impersonation", "The message appears to use a brand or institution identity in a suspicious claim or verification request.", Severity.HIGH),
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
