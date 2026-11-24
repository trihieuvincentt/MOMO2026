from pydantic import BaseModel, Field


class CleanDatasetRecord(BaseModel):
    source: str
    license_name: str
    source_row_id: str
    text: str = Field(min_length=1)
    normalized_text: str = Field(min_length=1)
    label: int | None = None
    category: str | None = None
    is_synthetic: bool = False
