from enum import StrEnum

from pydantic import BaseModel, Field


class URLScanStatus(StrEnum):
    SUCCESS = "success"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class URLResultMode(StrEnum):
    LIVE = "live"
    FIXTURE = "fixture"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


class URLScanRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class URLObservation(BaseModel):
    normalized_url: str
    hostname: str
    scheme: str
    notes: list[str] = Field(default_factory=list)
    is_local_or_private: bool = False


class URLScanResult(BaseModel):
    observation: URLObservation
    findings: list
    limitations: list[str] = Field(default_factory=list)
    status: URLScanStatus
    mode: URLResultMode
    lookup_source: str | None = None
    lookup_sources: list[str] = Field(default_factory=list)
