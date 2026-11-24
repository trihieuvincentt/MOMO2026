import re
import unicodedata
from collections.abc import Iterable

from backend.app.schemas.dataset import CleanDatasetRecord

_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_PHONE = re.compile(r"(?<!\d)(?:\+?84|0)(?:[ .-]?\d){8,10}(?!\d)")
_OTP = re.compile(r"\b(?:otp|one[- ]time password|mã xác thực|ma xac thuc)\s*[:#-]?\s*\d{4,8}\b", re.I)


def normalize_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    return " ".join(value.casefold().split())


def mask_sensitive_values(value: str) -> str:
    value = _OTP.sub("OTP [REDACTED]", value)
    value = _EMAIL.sub("[REDACTED_EMAIL]", value)
    return _PHONE.sub("[REDACTED_PHONE]", value)


def clean_records(
    rows: Iterable[dict],
    *,
    source: str,
    license_name: str,
    text_field: str,
    id_field: str,
    label_field: str | None = None,
    category_field: str | None = None,
    is_synthetic: bool = False,
) -> list[CleanDatasetRecord]:
    cleaned: list[CleanDatasetRecord] = []
    seen: set[str] = set()
    for row in rows:
        if text_field not in row:
            raise ValueError(f"Required text_field '{text_field}' is missing")
        if id_field not in row:
            raise ValueError(f"Required id_field '{id_field}' is missing")
        raw_text = str(row[text_field] or "").strip()
        normalized = normalize_text(raw_text)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        label = row.get(label_field) if label_field else None
        cleaned.append(
            CleanDatasetRecord(
                source=source,
                license_name=license_name,
                source_row_id=str(row[id_field]),
                text=mask_sensitive_values(raw_text),
                normalized_text=normalize_text(mask_sensitive_values(raw_text)),
                label=int(label) if label is not None and str(label).isdigit() else None,
                category=str(row[category_field]) if category_field and row.get(category_field) is not None else None,
                is_synthetic=is_synthetic,
            )
        )
    return cleaned
