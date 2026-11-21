from datetime import datetime, timezone
from enum import StrEnum

from pydantic import BaseModel, Field


class EvidenceType(StrEnum):
    MESSAGE = "message"
    URL = "url"
    IMAGE = "image"
    OCR_TEXT = "ocr_text"


class EvidenceItem(BaseModel):
    id: str
    type: EvidenceType
    content_reference: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
