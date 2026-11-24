import pytest

from backend.app.services.dataset_cleaner import clean_records, normalize_text, mask_sensitive_values


def test_normalize_text_collapses_spacing_and_case():
    assert normalize_text("  URGENT!\n Verify   Account  ") == "urgent! verify account"


def test_masks_obvious_otp_email_and_phone_values():
    value = "OTP 123456, email user@example.com, phone +84 912 345 678"
    masked = mask_sensitive_values(value)
    assert "123456" not in masked
    assert "user@example.com" not in masked
    assert "+84 912 345 678" not in masked
    assert "[REDACTED]" in masked


def test_clean_records_deduplicates_and_preserves_provenance():
    rows = [
        {"message_id": "a", "text": "Urgent verify account"},
        {"message_id": "b", "text": " urgent   verify account "},
    ]
    cleaned = clean_records(rows, source="sms", license_name="CC BY 4.0", text_field="text", id_field="message_id")
    assert len(cleaned) == 1
    assert cleaned[0].source == "sms"
    assert cleaned[0].source_row_id == "a"


def test_missing_required_column_fails_clearly():
    with pytest.raises(ValueError, match="text_field"):
        clean_records([{"message_id": "a"}], source="sms", license_name="CC BY 4.0", text_field="text", id_field="message_id")
