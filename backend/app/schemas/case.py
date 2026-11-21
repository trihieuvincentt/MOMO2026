from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field

from backend.app.schemas.evidence import EvidenceItem
from backend.app.schemas.finding import Finding


class CaseStatus(StrEnum):
    OPEN = "open"
    ANALYZED = "analyzed"
    ERROR = "error"


class Case(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: CaseStatus = CaseStatus.OPEN
    overall_risk: str | None = None
    summary: str | None = None
    evidence: list[EvidenceItem] = []
    findings: list[Finding] = []
