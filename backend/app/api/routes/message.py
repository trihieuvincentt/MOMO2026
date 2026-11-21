from fastapi import APIRouter

from backend.app.schemas.message import MessageScanRequest, MessageScanResult
from backend.app.services.message_scanner import analyze_message

router = APIRouter(prefix="/api/v1/message", tags=["message"])


@router.post("/analyze", response_model=MessageScanResult)
def analyze(request: MessageScanRequest) -> MessageScanResult:
    return analyze_message(request)
