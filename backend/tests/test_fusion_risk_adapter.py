from backend.app.services.evidence_fusion import EvidenceFusionResult, FusionReason
from backend.app.services.fusion_risk_adapter import fusion_to_risk_assessment


def test_no_known_signal_still_recommends_independent_verification():
    fusion = EvidenceFusionResult(
        category="no_known_signal_found",
        score=0,
        reasons=[],
        limitations=["No match is not proof of safety."],
    )

    risk = fusion_to_risk_assessment(fusion)

    assert risk.recommendations
    assert "independently" in risk.recommendations[0].action.lower()


def test_fusion_to_risk_assessment_preserves_reasons_and_unknowns():
    fusion = EvidenceFusionResult(
        category="high_risk",
        score=90,
        reasons=[FusionReason("Known-risk target", "reputation_provider", "high", 50)],
        unknowns=["Screenshot context limited"],
        limitations=["No automated transaction was performed."],
    )

    risk = fusion_to_risk_assessment(fusion)

    assert risk.category == "high_risk"
    assert risk.contributing_finding_ids == ["fusion-reputation_provider-0"]
    assert "Screenshot context limited" in risk.unknowns
    assert "Known-risk target" in risk.explanation
