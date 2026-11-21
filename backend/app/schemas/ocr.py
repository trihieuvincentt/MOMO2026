from enum import StrEnum

from pydantic import BaseModel, Field


class OCRSource(StrEnum):
    PADDLEOCR = "paddleocr"
    GEMINI_VISION = "gemini_vision"
    NONE = "none"


class OCRStatus(StrEnum):
    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class OCRExtraction(BaseModel):
    id: str
    extracted_text: str
    warnings: list[str] = Field(default_factory=list)
    status: OCRStatus
    ocr_source: OCRSource
    provider_notice: str | None = None
    retention_expires_at: str | None = None
