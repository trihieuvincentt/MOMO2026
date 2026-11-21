import pytest

from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.risk import RiskCategory, RecommendationPriority
from backend.app.services.recommendation_catalog import recommend_actions
from backend.app.services.risk_assessor import assess_risk


def make_finding(category: str, severity: Severity) -> Finding:
    return Finding(
        id="finding-1",
        category=category,
        description="indicator",
        evidence_item_id="evidence-1",
        source_type=FindingSource.RULE,
        verification_status=VerificationStatus.SUSPICIOUS_INDICATOR,
        severity=severity,
    )


@pytest.mark.parametrize(
    ("category", "priority"),
    [
        (RiskCategory.HIGH_RISK, RecommendationPriority.IMMEDIATE),
        (RiskCategory.ELEVATED_RISK, RecommendationPriority.HIGH),
        (RiskCategory.CAUTION, RecommendationPriority.NORMAL),
        (RiskCategory.NO_KNOWN_SIGNAL_FOUND, RecommendationPriority.NORMAL),
        (RiskCategory.INSUFFICIENT_INFORMATION, RecommendationPriority.HIGH),
    ],
)
def test_recommendations_have_safe_action_and_reason(category, priority):
    assessment = assess_risk([], ["success"])
    assessment = assessment.model_copy(update={"category": category})

    recommendations = recommend_actions(assessment, [])

    assert recommendations
    assert recommendations[0].priority == priority
    assert recommendations[0].action
    assert recommendations[0].reason
    assert "password" not in recommendations[0].action.lower()


def test_credential_finding_recommends_protective_action_without_repeating_secret():
    finding = make_finding("credential_request", Severity.HIGH)
    assessment = assess_risk([finding], ["success"])

    recommendations = recommend_actions(assessment, [finding])

    assert any("credential" in item.action.lower() for item in recommendations)
    assert all("otp" not in item.action.lower() for item in recommendations)
