from backend.app.services.evidence_fusion import EvidenceFusionResult
from backend.app.schemas.risk import Recommendation, RecommendationPriority, RiskAssessment, RiskCategory


_POLICY_VERSION = "2026-11-25.evidence-fusion.v1"
_CATEGORY_MAP = {
    "high_risk": RiskCategory.HIGH_RISK,
    "elevated_risk": RiskCategory.ELEVATED_RISK,
    "caution": RiskCategory.CAUTION,
    "no_known_signal_found": RiskCategory.NO_KNOWN_SIGNAL_FOUND,
    "insufficient_information": RiskCategory.INSUFFICIENT_INFORMATION,
}


def fusion_to_risk_assessment(result: EvidenceFusionResult) -> RiskAssessment:
    contributing_ids = [
        f"fusion-{reason.evidence_source}-{index}"
        for index, reason in enumerate(result.reasons)
    ]
    explanation = " ".join(reason.description for reason in result.reasons)
    if not explanation:
        explanation = "No corroborated evidence was available for the assessment."
    if result.score:
        explanation = f"Evidence fusion score {result.score}/100. {explanation}"
    recommendations = []
    if result.category in {"high_risk", "elevated_risk"}:
        recommendations.append(Recommendation(
            action="Do not enter credentials, OTPs, payment data, or send money through this website.",
            reason="The combined evidence contains suspicious or verified risk signals.",
            priority=RecommendationPriority.IMMEDIATE,
        ))
    elif result.category in {"insufficient_information", "no_known_signal_found", "caution"}:
        recommendations.append(Recommendation(
            action="Verify the website through an independently known official channel before entering information or proceeding.",
            reason=(
                "The available evidence is incomplete."
                if result.category == "insufficient_information"
                else "No signal or only limited signals were found; this is not proof that the website is safe."
            ),
            priority=RecommendationPriority.NORMAL,
        ))
    return RiskAssessment(
        category=_CATEGORY_MAP.get(result.category, RiskCategory.INSUFFICIENT_INFORMATION),
        explanation=explanation,
        contributing_finding_ids=contributing_ids,
        unknowns=result.unknowns,
        recommendations=recommendations,
        policy_version=_POLICY_VERSION,
    )
