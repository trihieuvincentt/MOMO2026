from pydantic import BaseModel, Field

from backend.app.schemas.case import Case, EvidenceScanStatus, EvidenceRelationship
from backend.app.schemas.artifact import CampaignMatch, ScamArtifact
from backend.app.schemas.finding import Finding
from backend.app.schemas.investigation import FindingExplanation
from backend.app.schemas.risk import Recommendation, RiskAssessment


class ReportEvidenceItem(BaseModel):
    id: str
    type: str
    content_reference: str | None
    status: EvidenceScanStatus | None = None


class ReportFinding(BaseModel):
    finding: Finding
    supported: bool

    @property
    def evidence_item_id(self) -> str | None:
        return self.finding.evidence_item_id


class InvestigationReport(BaseModel):
    case_id: str
    generated_at: str
    risk: RiskAssessment
    summary: str
    ai_summary: str | None = None
    evidence_items: list[ReportEvidenceItem] = Field(default_factory=list)
    artifacts: list[ScamArtifact] = Field(default_factory=list)
    campaign_matches: list[CampaignMatch] = Field(default_factory=list)
    findings: list[ReportFinding] = Field(default_factory=list)
    relationships: list[EvidenceRelationship] = Field(default_factory=list)
    scanner_statuses: list[ReportEvidenceItem] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    actions: list[Recommendation] = Field(default_factory=list)
