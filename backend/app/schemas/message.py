from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.finding import Finding


class ScannerStatus(StrEnum):
    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class MessageScanRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)
    language_hint: str | None = None

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("message text must not be blank")
        return value


class MessageScanResult(BaseModel):
    summary: str
    findings: list[Finding] = []
    limitations: list[str] = []
    status: ScannerStatus
