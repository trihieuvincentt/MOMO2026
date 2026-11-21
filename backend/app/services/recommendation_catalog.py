from backend.app.schemas.finding import Finding
from backend.app.schemas.risk import (
    Recommendation,
    RecommendationPriority,
    RiskAssessment,
    RiskCategory,
)


def recommend_actions(
    assessment: RiskAssessment,
    findings: list[Finding],
) -> list[Recommendation]:
    actions: list[Recommendation] = []
    if assessment.category == RiskCategory.HIGH_RISK:
        actions.append(
            Recommendation(
                action="Do not pay, click further, or share additional sensitive information.",
                reason="A verified high-risk finding is present in the assessment.",
                priority=RecommendationPriority.IMMEDIATE,
            )
        )
    elif assessment.category == RiskCategory.ELEVATED_RISK:
        actions.append(
            Recommendation(
                action="Pause the interaction and verify the organization through an independently found official channel.",
                reason="Strong or multiple suspicious indicators require independent verification.",
                priority=RecommendationPriority.HIGH,
            )
        )
    elif assessment.category == RiskCategory.INSUFFICIENT_INFORMATION:
        actions.append(
            Recommendation(
                action="Do not make an irreversible payment or account change until the missing checks are available.",
                reason="The available evidence is incomplete or one or more scanners failed.",
                priority=RecommendationPriority.HIGH,
            )
        )
    elif assessment.category == RiskCategory.CAUTION:
        actions.append(
            Recommendation(
                action="Pause before responding and verify the request using a trusted channel.",
                reason="A weaker suspicious indicator was found, but it is not conclusive by itself.",
                priority=RecommendationPriority.NORMAL,
            )
        )
    else:
        actions.append(
            Recommendation(
                action="Continue to use normal caution and verify unexpected requests independently.",
                reason="No known signal was found, which is not a guarantee of safety.",
                priority=RecommendationPriority.NORMAL,
            )
        )

    if any(finding.category == "credential_request" for finding in findings):
        actions.append(
            Recommendation(
                action="If sensitive account information was already shared, secure the affected credential and contact its official support channel.",
                reason="The case includes an indicator of an attempted credential request.",
                priority=RecommendationPriority.HIGH,
            )
        )
    if any(finding.category == "advance_fee" for finding in findings):
        actions.append(
            Recommendation(
                action="Do not send an upfront fee until the offer and recipient are independently verified.",
                reason="The case includes an indicator of an advance-fee request.",
                priority=RecommendationPriority.HIGH,
            )
        )
    return actions
