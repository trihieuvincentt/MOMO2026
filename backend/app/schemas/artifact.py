from enum import StrEnum

from pydantic import BaseModel, Field


class ArtifactType(StrEnum):
    BRAND = "brand"
    URL = "url"
    PHONE = "phone"
    AMOUNT = "amount"
    DISTINCTIVE_PHRASE = "distinctive_phrase"
    SCAM_PATTERN = "scam_pattern"


class ScamArtifact(BaseModel):
    type: ArtifactType
    normalized_value: str = Field(min_length=1, max_length=500)
    display_value: str = Field(min_length=1, max_length=500)
    source_evidence_id: str = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)


class CampaignMatch(BaseModel):
    case_ids: list[str] = Field(default_factory=list)
    shared_artifact_types: list[str] = Field(default_factory=list)
    shared_artifact_values: list[str] = Field(default_factory=list)
    score: int = Field(ge=1)
