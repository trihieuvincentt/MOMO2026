from backend.app.schemas.dataset import CleanDatasetRecord
from backend.app.services.dataset_features import extract_feature_families


def record(text, source="sms"):
    return CleanDatasetRecord(
        source=source,
        license_name="test",
        source_row_id="row-1",
        text=text,
        normalized_text=text.casefold(),
        is_synthetic=source == "synthetic",
    )


def test_extracts_multiple_feature_families():
    features = extract_feature_families(record("Urgent verify your account. Send OTP and click the link to claim your prize."))
    assert {"credential_request", "verification_phishing", "external_link_request", "prize_claim", "urgency"} <= set(features)


def test_feature_extraction_does_not_mark_benign_brand_mention():
    features = extract_feature_families(record("Facebook published a public developer documentation update."))
    assert "brand_impersonation" not in features


def test_catalog_preserves_source_provenance():
    features = extract_feature_families(record("Deposit now for guaranteed profit", source="synthetic"))
    assert features["investment_scam"][0]["source_row_id"] == "row-1"
    assert features["investment_scam"][0]["is_synthetic"] is True
