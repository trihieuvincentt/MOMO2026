from enum import StrEnum

from pydantic import BaseModel, Field


class RiskCategory(StrEnum):
    HIGH_RISK = "high_risk"
    ELEVATED_RISK = "elevated_risk"
    CAUTION = "caution"
    NO_KNOWN_SIGNAL_FOUND = "no_known_signal_found"
    INSUFFICIENT_INFORMATION = "insufficient_information"


class RecommendationPriority(StrEnum):
    IMMEDIATE = "immediate"
    HIGH = "high"
    NORMAL = "normal"


class Recommendation(BaseModel):
    action: str
    reason: str
    priority: RecommendationPriority


class RiskAssessment(BaseModel):
    category: RiskCategory
    explanation: str
    contributing_finding_ids: list[str] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    policy_version: str
