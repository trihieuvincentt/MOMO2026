from pydantic import BaseModel, Field


class FusionReasonResponse(BaseModel):
    description: str
    evidence_source: str
    severity: str
    score: int


class EvidenceFusionRequest(BaseModel):
    visual: dict | None = None
    content: dict | None = None
    links: dict | None = None
    reputation_matches: int = Field(default=0, ge=0, le=20)


class EvidenceFusionResponse(BaseModel):
    category: str
    score: int
    reasons: list[FusionReasonResponse]
    unknowns: list[str]
    limitations: list[str]
