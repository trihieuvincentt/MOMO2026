from enum import StrEnum

from pydantic import BaseModel


class FindingSource(StrEnum):
    USER_INPUT = "user_input"
    RULE = "rule"
    REPUTATION_API = "reputation_api"
    OCR = "ocr"
    LLM = "llm"
    KNOWLEDGE_BASE = "knowledge_base"


class VerificationStatus(StrEnum):
    VERIFIED_MATCH = "verified_match"
    SUSPICIOUS_INDICATOR = "suspicious_indicator"
    UNVERIFIED = "unverified"
    NO_SIGNAL_FOUND = "no_signal_found"


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Finding(BaseModel):
    id: str
    category: str
    description: str
    evidence_item_id: str | None = None
    evidence_excerpt: str | None = None
    source_type: FindingSource
    verification_status: VerificationStatus
    severity: Severity
    limitations: list[str] = []
