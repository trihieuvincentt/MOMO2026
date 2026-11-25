from backend.app.adapters.gemini_visual import VisualAnalysis, VisualForm, VisualIndicator
from backend.app.services.content_extractor import ExtractedForm, ExtractedLink, WebsiteContent
from backend.app.services.evidence_fusion import EvidenceFusionService
from backend.app.services.link_analyzer import AnalyzedLink, LinkAnalysisResult
from backend.app.services.visual_analysis import VisualAnalysisResult


def test_fusion_raises_risk_from_independent_evidence_sources():
    visual = VisualAnalysisResult(
        status="success",
        site_type="banking",
        detected_brands=["Example Bank"],
        forms=[VisualForm("login", ["password", "otp"])],
        indicators=[VisualIndicator("brand_impersonation", "Looks like a bank login", 0.92)],
        sensitive_data_requested=["password", "otp"],
    )
    links = LinkAnalysisResult([
        AnalyzedLink(
            text="Login", url="https://fake.example/login", domain="fake.example",
            relationship="external", role="login", indicators=("brand_domain_mismatch",),
            severity="high", requires_deep_analysis=True,
        )
    ], ["https://fake.example/login"])

    result = EvidenceFusionService().fuse(
        visual=visual,
        content=None,
        links=links,
        reputation_matches=1,
    )

    assert result.category == "high_risk"
    assert result.score >= 80
    assert len(result.reasons) >= 3
    assert all(reason.evidence_source for reason in result.reasons)
    assert any("domain" in reason.description.lower() for reason in result.reasons)


def test_visual_only_never_becomes_definitive_high_risk():
    visual = VisualAnalysisResult(
        status="success",
        site_type="banking",
        detected_brands=["Example Bank"],
        indicators=[VisualIndicator("brand_impersonation", "Similar colors", 0.95)],
    )

    result = EvidenceFusionService().fuse(visual=visual, content=None, links=None)

    assert result.category in {"caution", "elevated_risk"}
    assert result.category != "high_risk"
    assert any("visual" in limitation.lower() for limitation in result.limitations)


def test_unavailable_inputs_are_explicit_unknowns():
    result = EvidenceFusionService().fuse(visual=None, content=None, links=None)

    assert result.category == "insufficient_information"
    assert result.score == 0
    assert result.unknowns
    assert result.limitations
