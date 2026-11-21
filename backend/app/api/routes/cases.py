from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.schemas.case import Case
from backend.app.schemas.evidence import EvidenceItem, EvidenceType
from backend.app.schemas.report import InvestigationReport
from backend.app.services.case_service import (
    DuplicateEvidenceError,
    InMemoryCaseRepository,
    add_evidence,
    analyze_case,
    create_case,
    get_case,
)
from backend.app.services.report_builder import build_report

router = APIRouter(prefix="/api/v1/cases", tags=["cases"])
case_repository = InMemoryCaseRepository()


class EvidenceItemRequest(BaseModel):
    type: EvidenceType
    content_reference: str = Field(min_length=1, max_length=20_000)


@router.post("", response_model=Case, status_code=201)
def create_case_route() -> Case:
    return create_case(case_repository)


@router.post("/{case_id}/evidence", response_model=EvidenceItem, status_code=201)
def add_evidence_route(case_id: str, request: EvidenceItemRequest) -> EvidenceItem:
    try:
        return add_evidence(case_repository, case_id, request.type, request.content_reference)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    except DuplicateEvidenceError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/{case_id}/analyze", response_model=Case)
def analyze_case_route(case_id: str) -> Case:
    try:
        return analyze_case(case_repository, case_id).case
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc


@router.get("/{case_id}/report", response_model=InvestigationReport)
def get_report_route(case_id: str) -> InvestigationReport:
    try:
        case = get_case(case_repository, case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
    if case.risk_assessment is None:
        raise HTTPException(status_code=409, detail="Case must be analyzed before a report is available")
    return build_report(case, case.risk_assessment, case.risk_assessment.recommendations)


@router.get("/{case_id}", response_model=Case)
def get_case_route(case_id: str) -> Case:
    try:
        return get_case(case_repository, case_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Case not found") from exc
