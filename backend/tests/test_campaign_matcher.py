from backend.app.schemas.artifact import ScamArtifact
from backend.app.schemas.case import Case
from backend.app.schemas.evidence import EvidenceItem, EvidenceType
from backend.app.services.campaign_matcher import match_campaigns


def artifact(kind, value, evidence="e-1"):
    return ScamArtifact(
        type=kind,
        normalized_value=value,
        display_value=value,
        source_evidence_id=evidence,
        confidence=0.9,
    )


def case(case_id, artifacts):
    evidence_ids = {artifact.source_evidence_id for artifact in artifacts}
    evidence = [EvidenceItem(id=evidence_id, type=EvidenceType.MESSAGE, content_reference="safe evidence") for evidence_id in evidence_ids if evidence_id != "missing"]
    return Case(id=case_id, evidence=evidence, artifacts=artifacts)


def test_requires_two_shared_artifacts_for_campaign_match():
    current = case("current", [artifact("brand", "facebook"), artifact("scam_pattern", "prize_claim")])
    prior = case("prior", [artifact("brand", "facebook"), artifact("scam_pattern", "prize_claim")])

    matches = match_campaigns(current, [current, prior])

    assert len(matches) == 1
    assert matches[0].case_ids == ["prior"]
    assert set(matches[0].shared_artifact_types) == {"brand", "scam_pattern"}


def test_exact_url_or_phone_can_match_with_one_shared_artifact():
    current = case("current", [artifact("url", "https://evil.example/win")])
    prior = case("prior", [artifact("url", "https://evil.example/win")])

    matches = match_campaigns(current, [prior])

    assert len(matches) == 1
    assert matches[0].score >= 1


def test_excludes_same_case_and_unsupported_artifacts():
    current = case("current", [artifact("brand", "facebook")])
    unsupported = case("prior", [artifact("brand", "facebook", evidence="missing")])

    assert match_campaigns(current, [current, unsupported]) == []
