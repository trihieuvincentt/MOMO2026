from dataclasses import dataclass, field

from backend.app.services.content_extractor import WebsiteContent
from backend.app.services.link_analyzer import LinkAnalysisResult
from backend.app.services.visual_analysis import VisualAnalysisResult


@dataclass(frozen=True)
class FusionReason:
    description: str
    evidence_source: str
    severity: str
    score: int


@dataclass(frozen=True)
class EvidenceFusionResult:
    category: str
    score: int
    reasons: list[FusionReason] = field(default_factory=list)
    unknowns: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)


class EvidenceFusionService:
    def fuse(
        self,
        *,
        visual: VisualAnalysisResult | None,
        content: WebsiteContent | None,
        links: LinkAnalysisResult | None,
        reputation_matches: int = 0,
    ) -> EvidenceFusionResult:
        score = 0
        reasons: list[FusionReason] = []
        unknowns: list[str] = []
        limitations: list[str] = []

        if visual is None or visual.status != "success":
            unknowns.append("Visual analysis was unavailable or degraded.")
        elif visual.indicators:
            for indicator in visual.indicators:
                points = round(20 * indicator.confidence)
                score += points
                reasons.append(FusionReason(
                    description=indicator.description,
                    evidence_source="visual_analysis",
                    severity="medium",
                    score=points,
                ))
            if visual.sensitive_data_requested:
                points = min(20, 8 + len(visual.sensitive_data_requested) * 4)
                score += points
                reasons.append(FusionReason(
                    description=f"The visual analysis identified sensitive fields: {', '.join(visual.sensitive_data_requested)}.",
                    evidence_source="visual_analysis",
                    severity="high",
                    score=points,
                ))
            limitations.append("Visual similarity alone is not proof of phishing.")

        if content is None:
            unknowns.append("Rendered website content was not available.")
        else:
            sensitive_fields = [
                field.name for form in content.forms for field in form.fields
                if field.sensitivity == "sensitive"
            ]
            if sensitive_fields:
                points = min(25, 10 + len(set(sensitive_fields)) * 3)
                score += points
                reasons.append(FusionReason(
                    description=f"Rendered forms request sensitive fields: {', '.join(sorted(set(sensitive_fields)))}.",
                    evidence_source="content_extraction",
                    severity="high",
                    score=points,
                ))

        if links is None:
            unknowns.append("Link relationship analysis was not available.")
        else:
            for link in links.links:
                if "brand_domain_mismatch" in link.indicators:
                    score += 30
                    reasons.append(FusionReason(
                        description=f"Sensitive link {link.url} does not match the claimed brand domain.",
                        evidence_source="link_domain_analysis",
                        severity="high",
                        score=30,
                    ))
                elif link.relationship == "external" and link.role in {"login", "registration", "verification", "payment"}:
                    score += 12
                    reasons.append(FusionReason(
                        description=f"The {link.role} action leads to an external domain: {link.domain}.",
                        evidence_source="link_domain_analysis",
                        severity="medium",
                        score=12,
                    ))
            limitations.extend(links.limitations)

        if reputation_matches:
            points = min(50, reputation_matches * 50)
            score += points
            reasons.append(FusionReason(
                description=f"Reputation analysis reported {reputation_matches} known-risk target(s).",
                evidence_source="reputation_provider",
                severity="high",
                score=points,
            ))
        elif links is not None:
            limitations.append("No reputation match is not a guarantee of safety.")

        score = min(score, 100)
        if not reasons and len(unknowns) >= 3:
            category = "insufficient_information"
            limitations.append("Insufficient evidence was available for a meaningful risk assessment.")
        elif reputation_matches or score >= 80:
            category = "high_risk"
        elif score >= 40:
            category = "elevated_risk"
        elif score > 0:
            category = "caution"
        else:
            category = "no_known_signal_found"
            limitations.append("No known signal found is not a guarantee of safety.")

        if visual and visual.indicators and not links and not content:
            category = "elevated_risk" if score >= 15 else "caution"
            limitations.append("Visual evidence was not corroborated by content, link, or reputation analysis.")

        return EvidenceFusionResult(
            category=category,
            score=score,
            reasons=reasons,
            unknowns=unknowns,
            limitations=list(dict.fromkeys(limitations)),
        )
