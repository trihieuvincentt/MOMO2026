from backend.app.schemas.evidence import EvidenceItem, EvidenceType
from backend.app.services.artifact_extractor import extract_artifacts


def test_extracts_vietnamese_prize_campaign_artifacts():
    evidence = [
        EvidenceItem(
            id="e-message",
            type=EvidenceType.MESSAGE,
            content_reference=(
                "Chúc mừng tài khoản Facebook đã trúng giải nhất. "
                "Xe máy Piaggio Liberty và phiếu quà tặng 55.000.000 VNĐ. "
                "Mã số may mắn 02079697, truy cập ngay website."
            ),
        )
    ]

    artifacts = extract_artifacts(evidence)
    values = {(artifact.type, artifact.normalized_value) for artifact in artifacts}

    assert ("brand", "facebook") in values
    assert ("amount", "55000000 vnd") in values
    assert ("scam_pattern", "prize_claim") in values
    assert any(artifact.source_evidence_id == "e-message" for artifact in artifacts)


def test_normalizes_urls_and_phones_and_deduplicates():
    evidence = [
        EvidenceItem(
            id="e-message",
            type=EvidenceType.MESSAGE,
            content_reference="Visit HTTPS://Example.COM/win and call +84 912 345 678.",
        )
    ]

    artifacts = extract_artifacts(evidence)
    values = {(artifact.type, artifact.normalized_value) for artifact in artifacts}

    assert ("url", "https://example.com/win") in values
    assert ("phone", "+84912345678") in values
    assert len(artifacts) == len({(a.type, a.normalized_value, a.source_evidence_id) for a in artifacts})


def test_extracts_credential_and_account_suspension_patterns():
    evidence = [
        EvidenceItem(
            id="e-message",
            type=EvidenceType.MESSAGE,
            content_reference="URGENT! Send your OTP and password now or your bank account will be suspended.",
        )
    ]

    artifacts = extract_artifacts(evidence)
    values = {(artifact.type, artifact.normalized_value) for artifact in artifacts}

    assert ("scam_pattern", "credential_request") in values
    assert ("scam_pattern", "account_suspension") in values
    assert ("distinctive_phrase", "urgent account suspension") in values


def test_does_not_extract_sensitive_credential_values():
    evidence = [
        EvidenceItem(
            id="e-message",
            type=EvidenceType.MESSAGE,
            content_reference="Your OTP is 123456 and password is SecretPass123.",
        )
    ]

    artifacts = extract_artifacts(evidence)

    assert not any(artifact.normalized_value in {"123456", "secretpass123"} for artifact in artifacts)
