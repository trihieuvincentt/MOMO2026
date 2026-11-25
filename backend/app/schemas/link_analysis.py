from pydantic import BaseModel, Field


class LinkAnalysisRequest(BaseModel):
    source_url: str = Field(min_length=1, max_length=2048)
    links: list[dict] = Field(default_factory=list)
    claimed_brands: list[str] = Field(default_factory=list)


class AnalyzedLinkResponse(BaseModel):
    text: str
    url: str
    domain: str
    relationship: str
    role: str | None = None
    indicators: list[str] = Field(default_factory=list)
    severity: str
    requires_deep_analysis: bool
    reputation_source: str | None = None
    reputation_matched: bool | None = None
    reputation_details: str | None = None


class LinkAnalysisResponse(BaseModel):
    links: list[AnalyzedLinkResponse]
    deep_analysis_targets: list[str]
    limitations: list[str] = Field(default_factory=list)
