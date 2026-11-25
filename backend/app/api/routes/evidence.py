from fastapi import APIRouter

from backend.app.schemas.evidence_fusion import (
    EvidenceFusionRequest,
    EvidenceFusionResponse,
    FusionReasonResponse,
)
from backend.app.services.content_extractor import ExtractedForm, FormField, WebsiteContent
from backend.app.services.evidence_fusion import EvidenceFusionService
from backend.app.services.link_analyzer import AnalyzedLink, LinkAnalysisResult
from backend.app.services.visual_analysis import VisualAnalysisResult
from backend.app.adapters.gemini_visual import VisualForm, VisualIndicator

router = APIRouter(prefix="/api/v1/evidence", tags=["evidence"])


def _visual(value: dict | None) -> VisualAnalysisResult | None:
    if value is None:
        return None
    return VisualAnalysisResult(
        status=str(value.get("status", "success")),
        site_type=str(value.get("site_type", "unknown")),
        detected_brands=[str(item) for item in value.get("detected_brands", [])],
        forms=[VisualForm(str(item.get("purpose", "unknown")), [str(field) for field in item.get("fields", [])]) for item in value.get("forms", [])],
        indicators=[VisualIndicator(str(item.get("category", "unknown")), str(item.get("description", "")), float(item.get("confidence", 0)), item.get("evidence")) for item in value.get("indicators", [])],
        sensitive_data_requested=[str(item) for item in value.get("sensitive_data_requested", [])],
        limitations=[str(item) for item in value.get("limitations", [])],
    )


def _content(value: dict | None) -> WebsiteContent | None:
    if value is None:
        return None
    forms = []
    for form in value.get("forms", []):
        fields = [FormField(str(field.get("name", "")), str(field.get("input_type", "text")), str(field.get("sensitivity", "normal"))) for field in form.get("fields", [])]
        forms.append(ExtractedForm(str(form.get("action_url", "")), str(form.get("method", "get")), tuple(fields)))
    return WebsiteContent(
        title=str(value.get("title", "")),
        meta_description=str(value.get("meta_description", "")),
        headings=[str(item) for item in value.get("headings", [])],
        visible_text=str(value.get("visible_text", "")),
        forms=forms,
        links=[],
    )


def _links(value: dict | None) -> LinkAnalysisResult | None:
    if value is None:
        return None
    analyzed = [
        AnalyzedLink(
            text=str(item.get("text", "")),
            url=str(item.get("url", "")),
            domain=str(item.get("domain", "")),
            relationship=str(item.get("relationship", "external")),
            role=item.get("role"),
            indicators=tuple(str(indicator) for indicator in item.get("indicators", [])),
            severity=str(item.get("severity", "low")),
            requires_deep_analysis=bool(item.get("requires_deep_analysis", False)),
            reputation_source=item.get("reputation_source"),
            reputation_matched=item.get("reputation_matched"),
            reputation_details=item.get("reputation_details"),
        )
        for item in value.get("links", [])
    ]
    return LinkAnalysisResult(analyzed, [str(item) for item in value.get("deep_analysis_targets", [])], [str(item) for item in value.get("limitations", [])])


@router.post("/fuse", response_model=EvidenceFusionResponse)
def fuse_evidence(request: EvidenceFusionRequest) -> EvidenceFusionResponse:
    result = EvidenceFusionService().fuse(
        visual=_visual(request.visual),
        content=_content(request.content),
        links=_links(request.links),
        reputation_matches=request.reputation_matches,
    )
    return EvidenceFusionResponse(
        category=result.category,
        score=result.score,
        reasons=[FusionReasonResponse(**reason.__dict__) for reason in result.reasons],
        unknowns=result.unknowns,
        limitations=result.limitations,
    )
