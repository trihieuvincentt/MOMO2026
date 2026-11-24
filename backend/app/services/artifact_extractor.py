import re
from urllib.parse import urlsplit, urlunsplit

from backend.app.schemas.artifact import ArtifactType, ScamArtifact
from backend.app.schemas.evidence import EvidenceItem, EvidenceType

_URL_RE = re.compile(r"https?://[^\s<>\]\[)]+", re.IGNORECASE)
_PHONE_RE = re.compile(r"(?<!\d)(?:\+84|0)(?:[ .-]?\d){8,10}(?!\d)")
_AMOUNT_RE = re.compile(r"(?<!\d)(\d{1,3}(?:[.,]\d{3})+|\d+)(?:\s*)(VNĐ|VND|đ|USD|\$)(?!\w)", re.IGNORECASE)
_BRANDS = ("facebook", "mobifone", "mobi fone", "zalo", "vietcombank", "techcombank")
_PRIZE_TERMS = ("trúng giải", "giải nhất", "giải thưởng", "chúc mừng", "may mắn")
_CREDENTIAL_TERMS = ("otp", "one-time password", "password", "mật khẩu", "recovery code", "mã xác thực")
_SUSPENSION_TERMS = ("account will be suspended", "tài khoản sẽ bị khóa", "tài khoản sẽ bị đình chỉ", "account suspended")


def _artifact(kind: ArtifactType, value: str, source_id: str, confidence: float = 0.9) -> ScamArtifact:
    return ScamArtifact(
        type=kind,
        normalized_value=value.strip().lower(),
        display_value=value.strip(),
        source_evidence_id=source_id,
        confidence=confidence,
    )


def _normalize_url(value: str) -> str:
    parts = urlsplit(value.rstrip(".,;:!?"))
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or "", parts.query, ""))


def _normalize_phone(value: str) -> str:
    compact = re.sub(r"[ .()-]", "", value)
    if compact.startswith("0084"):
        compact = "+84" + compact[4:]
    elif compact.startswith("0"):
        compact = "+84" + compact[1:]
    return compact


def _normalize_amount(number: str, currency: str) -> str:
    digits = re.sub(r"[.,]", "", number)
    currency_value = "vnd" if currency.lower() in {"vnđ", "vnd", "đ"} else currency.lower()
    return f"{digits} {currency_value}"


def extract_artifacts(evidence: list[EvidenceItem]) -> list[ScamArtifact]:
    artifacts: list[ScamArtifact] = []
    seen: set[tuple[str, str, str]] = set()
    for item in evidence:
        if item.type not in {EvidenceType.MESSAGE, EvidenceType.OCR_TEXT, EvidenceType.URL}:
            continue
        text = item.content_reference or ""
        candidates: list[ScamArtifact] = []
        for match in _URL_RE.finditer(text):
            value = _normalize_url(match.group(0))
            candidates.append(_artifact(ArtifactType.URL, value, item.id, 1.0))
        for match in _PHONE_RE.finditer(text):
            value = _normalize_phone(match.group(0))
            candidates.append(_artifact(ArtifactType.PHONE, value, item.id, 0.95))
        for match in _AMOUNT_RE.finditer(text):
            value = _normalize_amount(match.group(1), match.group(2))
            candidates.append(ScamArtifact(type=ArtifactType.AMOUNT, normalized_value=value, display_value=match.group(0), source_evidence_id=item.id, confidence=0.9))
        lower_text = text.lower()
        for brand in _BRANDS:
            if brand in lower_text:
                candidates.append(_artifact(ArtifactType.BRAND, brand, item.id, 0.8))
        if any(term in lower_text for term in _PRIZE_TERMS) and any(term in lower_text for term in ("xe máy", "phiếu quà tặng", "tiền mặt", "website", "truy cập")):
            candidates.append(_artifact(ArtifactType.SCAM_PATTERN, "prize_claim", item.id, 0.95))
        if any(term in lower_text for term in _CREDENTIAL_TERMS):
            candidates.append(_artifact(ArtifactType.SCAM_PATTERN, "credential_request", item.id, 0.95))
        if any(term in lower_text for term in _SUSPENSION_TERMS):
            candidates.append(_artifact(ArtifactType.SCAM_PATTERN, "account_suspension", item.id, 0.9))
        if any(term in lower_text for term in ("urgent", "khẩn cấp")) and any(term in lower_text for term in _SUSPENSION_TERMS):
            candidates.append(_artifact(ArtifactType.DISTINCTIVE_PHRASE, "urgent account suspension", item.id, 0.85))
        for phrase in ("mã số may mắn", "truy cập ngay", "lucky code"):
            if phrase in lower_text:
                candidates.append(_artifact(ArtifactType.DISTINCTIVE_PHRASE, phrase, item.id, 0.85))
        for candidate in candidates:
            key = (candidate.type.value, candidate.normalized_value, candidate.source_evidence_id)
            if key not in seen:
                seen.add(key)
                artifacts.append(candidate)
    return artifacts
