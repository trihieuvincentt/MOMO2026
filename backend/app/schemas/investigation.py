from enum import StrEnum

from pydantic import BaseModel, Field


class InvestigationStatus(StrEnum):
    SUCCESS = "success"
    DEGRADED = "degraded"
    ERROR = "error"


class FindingExplanation(BaseModel):
    finding_id: str
    explanation: str = Field(min_length=1, max_length=4_000)


class SupportedRelationship(BaseModel):
    source_evidence_id: str
    target_evidence_id: str
    basis: str = Field(min_length=1, max_length=1_000)


class InvestigationModelOutput(BaseModel):
    summary: str = Field(min_length=1, max_length=8_000)
    finding_explanations: list[FindingExplanation]
    relationships: list[SupportedRelationship]
    unknowns: list[str]


class InvestigationResult(BaseModel):
    status: InvestigationStatus
    summary: str
    finding_explanations: list[FindingExplanation] = Field(default_factory=list)
    relationships: list[SupportedRelationship] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
