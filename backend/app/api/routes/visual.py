import os

from fastapi import APIRouter, HTTPException
from starlette.concurrency import run_in_threadpool

from backend.app.adapters.gemini_visual import GeminiVisualAnalyzer
from backend.app.config import get_investigation_model
from backend.app.schemas.visual_analysis import (
    VisualAnalysisRequest,
    VisualAnalysisResponse,
)
from backend.app.services.browser_snapshot import BrowserSnapshotError, BrowserSnapshotService
from backend.app.services.visual_analysis import VisualAnalysisService

router = APIRouter(prefix="/api/v1/visual", tags=["visual"])


def get_visual_analyzer():
    model = get_investigation_model()
    if model is None:
        return None
    return GeminiVisualAnalyzer(
        api_key=os.getenv("GEMINI_API_KEY", ""),
        model_name=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    )


@router.post("/analyze", response_model=VisualAnalysisResponse)
async def analyze_visual_route(request: VisualAnalysisRequest) -> VisualAnalysisResponse:
    try:
        snapshot = await run_in_threadpool(BrowserSnapshotService().capture, request.url)
    except BrowserSnapshotError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    result = await run_in_threadpool(
        VisualAnalysisService(get_visual_analyzer()).analyze,
        snapshot,
        claimed_brands=request.claimed_brands,
        deterministic_context=request.deterministic_context,
    )
    return VisualAnalysisResponse(
        status=result.status,
        site_type=result.site_type,
        detected_brands=result.detected_brands,
        forms=[{"purpose": form.purpose, "fields": form.fields} for form in result.forms],
        indicators=[indicator.__dict__ for indicator in result.indicators],
        sensitive_data_requested=result.sensitive_data_requested,
        limitations=result.limitations,
        screenshot_url=result.screenshot_url,
        model_name=result.model_name,
        normalized_url=snapshot.normalized_url,
        final_url=snapshot.final_url,
        title=snapshot.title,
    )
