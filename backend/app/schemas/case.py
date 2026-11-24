from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field

from backend.app.schemas.evidence import EvidenceItem
from backend.app.schemas.finding import Finding
from backend.app.schemas.artifact import ScamArtifact
from backend.app.schemas.investigation import InvestigationResult
from backend.app.schemas.risk import RiskAssessment


class CaseStatus(StrEnum):
    OPEN = "open"
    ANALYZED = "analyzed"
    ERROR = "error"


class EvidenceScanStatus(StrEnum):
    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class EvidenceRelationship(BaseModel):
    source_evidence_id: str
    target_evidence_id: str
    basis: str


class Case(BaseModel):
    id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: CaseStatus = CaseStatus.OPEN
    overall_risk: str | None = None
    summary: str | None = None
    evidence: list[EvidenceItem] = Field(default_factory=list)
    artifacts: list[ScamArtifact] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    scanner_statuses: dict[str, EvidenceScanStatus] = Field(default_factory=dict)
    relationships: list[EvidenceRelationship] = Field(default_factory=list)
    risk_assessment: RiskAssessment | None = None
    investigation: InvestigationResult | None = None
