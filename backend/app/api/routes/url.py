from fastapi import APIRouter, HTTPException, Query

from backend.app.schemas.url import URLScanRequest, URLScanResult
from backend.app.services.url_scanner import scan_url

router = APIRouter(prefix="/api/v1/url", tags=["url"])


@router.post("/analyze", response_model=URLScanResult)
def analyze_url(
    request: URLScanRequest,
    fixture_mode: bool = Query(default=False),
) -> URLScanResult:
    try:
        return scan_url(request.url, provider=None, fixture_mode=fixture_mode)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
