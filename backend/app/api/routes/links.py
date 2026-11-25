from fastapi import APIRouter, HTTPException

from backend.app.schemas.link_analysis import (
    AnalyzedLinkResponse,
    LinkAnalysisRequest,
    LinkAnalysisResponse,
)
from backend.app.services.content_extractor import ExtractedLink, WebsiteContent
from backend.app.services.link_analyzer import analyze_links
from backend.app.services.url_security import URLSecurityError, validate_fetch_target

router = APIRouter(prefix="/api/v1/links", tags=["links"])


@router.post("/analyze", response_model=LinkAnalysisResponse)
def analyze_link_relationships(request: LinkAnalysisRequest) -> LinkAnalysisResponse:
    try:
        source_url = validate_fetch_target(request.source_url).normalized_url
    except URLSecurityError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    content = WebsiteContent(
        title="",
        meta_description="",
        headings=[],
        visible_text="",
        links=[
            ExtractedLink(
                text=str(item.get("text", "")),
                url=str(item.get("url", "")),
                domain=str(item.get("domain", "")),
                rel=tuple(item.get("rel", ())),
                target=item.get("target"),
                is_internal=bool(item.get("is_internal", False)),
                role=item.get("role"),
            )
            for item in request.links
            if item.get("url")
        ],
    )
    result = analyze_links(
        content,
        source_url=source_url,
        claimed_brands=request.claimed_brands,
    )
    return LinkAnalysisResponse(
        links=[AnalyzedLinkResponse(**link.__dict__) for link in result.links],
        deep_analysis_targets=result.deep_analysis_targets,
        limitations=result.limitations,
    )
