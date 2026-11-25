from pydantic import BaseModel, Field


class VisualAnalysisRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    claimed_brands: list[str] = Field(default_factory=list, max_length=20)
    deterministic_context: str = Field(default="", max_length=4000)


class VisualIndicatorResponse(BaseModel):
    category: str
    description: str
    confidence: float
    evidence: str | None = None


class VisualFormResponse(BaseModel):
    purpose: str
    fields: list[str]


class VisualAnalysisResponse(BaseModel):
    status: str
    site_type: str
    detected_brands: list[str]
    forms: list[VisualFormResponse]
    indicators: list[VisualIndicatorResponse]
    sensitive_data_requested: list[str]
    limitations: list[str]
    screenshot_url: str | None = None
    model_name: str | None = None
    normalized_url: str | None = None
    final_url: str | None = None
    title: str | None = None
