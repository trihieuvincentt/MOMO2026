from copy import deepcopy
from dataclasses import dataclass
from secrets import token_urlsafe
from typing import Callable, Protocol

from backend.app.config import get_reputation_provider
from backend.app.schemas.case import Case, CaseStatus, EvidenceScanStatus, EvidenceRelationship
from backend.app.schemas.evidence import EvidenceItem, EvidenceType
from backend.app.schemas.finding import Finding
from backend.app.schemas.message import MessageScanRequest, MessageScanResult, ScannerStatus
from backend.app.schemas.url import URLScanResult
from backend.app.services.message_scanner import analyze_message
from backend.app.services.recommendation_catalog import recommend_actions
from backend.app.services.risk_assessor import assess_risk
from backend.app.services.url_scanner import scan_url


class DuplicateEvidenceError(ValueError):
    """The same evidence was already added to a case."""


class CaseRepository(Protocol):
    def save(self, case: Case) -> None: ...

    def get(self, case_id: str) -> Case: ...


class InMemoryCaseRepository:
    def __init__(self) -> None:
        self._cases: dict[str, Case] = {}

    def save(self, case: Case) -> None:
        self._cases[case.id] = deepcopy(case)

    def get(self, case_id: str) -> Case:
        if case_id not in self._cases:
            raise KeyError(case_id)
        return deepcopy(self._cases[case_id])

    def clear(self) -> None:
        self._cases.clear()


def _default_message_scanner(text: str) -> MessageScanResult:
    return analyze_message(MessageScanRequest(text=text))


def _default_url_scanner(value: str) -> URLScanResult:
    return scan_url(value, get_reputation_provider())


@dataclass(frozen=True)
class ScannerRegistry:
    message: Callable[[str], MessageScanResult] = _default_message_scanner
    url: Callable[[str], URLScanResult] = _default_url_scanner


@dataclass(frozen=True)
class CaseAnalysisResult:
    case: Case


def create_case(repository: CaseRepository) -> Case:
    case = Case(id=f"case-{token_urlsafe(16)}")
    repository.save(case)
    return deepcopy(case)


def get_case(repository: CaseRepository, case_id: str) -> Case:
    return repository.get(case_id)


def add_evidence(
    repository: CaseRepository,
    case_id: str,
    evidence_type: EvidenceType,
    content_reference: str,
) -> EvidenceItem:
    if not content_reference.strip():
        raise ValueError("Evidence content is required")
    case = repository.get(case_id)
    if any(
        item.type == evidence_type and item.content_reference == content_reference
        for item in case.evidence
    ):
        raise DuplicateEvidenceError("Equivalent evidence already exists in this case")

    item = EvidenceItem(
        id=f"evidence-{token_urlsafe(12)}",
        type=evidence_type,
        content_reference=content_reference,
    )
    case.evidence.append(item)
    repository.save(case)
    return deepcopy(item)


def _status(value: str) -> EvidenceScanStatus:
    if value == ScannerStatus.SUCCESS:
        return EvidenceScanStatus.SUCCESS
    if value == ScannerStatus.UNAVAILABLE:
        return EvidenceScanStatus.UNAVAILABLE
    return EvidenceScanStatus.ERROR


def _attach_findings(case: Case, evidence: EvidenceItem, findings: list[Finding]) -> None:
    case.findings.extend(
        finding.model_copy(update={"evidence_item_id": evidence.id})
        for finding in findings
    )


def _record_relationships(case: Case) -> None:
    messages = [item for item in case.evidence if item.type == EvidenceType.MESSAGE]
    urls = [item for item in case.evidence if item.type == EvidenceType.URL]
    case.relationships = []
    for message in messages:
        for url in urls:
            if url.content_reference and url.content_reference in (message.content_reference or ""):
                case.relationships.append(
                    EvidenceRelationship(
                        source_evidence_id=message.id,
                        target_evidence_id=url.id,
                        basis="exact URL appears in message evidence",
                    )
                )


def analyze_case(
    repository: CaseRepository,
    case_id: str,
    scanners: ScannerRegistry | None = None,
) -> CaseAnalysisResult:
    case = repository.get(case_id)
    registry = scanners or ScannerRegistry()
    case.findings = []
    successful = False

    for evidence in case.evidence:
        content = evidence.content_reference or ""
        try:
            if evidence.type in {EvidenceType.MESSAGE, EvidenceType.OCR_TEXT}:
                result = registry.message(content)
                case.scanner_statuses[evidence.id] = _status(result.status)
                if result.status == ScannerStatus.SUCCESS:
                    successful = True
                _attach_findings(case, evidence, result.findings)
            elif evidence.type == EvidenceType.URL:
                result = registry.url(content)
                case.scanner_statuses[evidence.id] = _status(result.status)
                if result.status == "success":
                    successful = True
                _attach_findings(case, evidence, result.findings)
            else:
                case.scanner_statuses[evidence.id] = EvidenceScanStatus.UNAVAILABLE
        except TimeoutError:
            case.scanner_statuses[evidence.id] = EvidenceScanStatus.UNAVAILABLE
        except Exception:
            case.scanner_statuses[evidence.id] = EvidenceScanStatus.ERROR

    _record_relationships(case)
    case.risk_assessment = assess_risk(
        case.findings,
        list(case.scanner_statuses.values()),
    )
    case.risk_assessment.recommendations = recommend_actions(
        case.risk_assessment,
        case.findings,
    )
    case.overall_risk = case.risk_assessment.category.value
    case.summary = case.risk_assessment.explanation
    case.status = CaseStatus.ANALYZED if successful else CaseStatus.ERROR
    repository.save(case)
    return CaseAnalysisResult(case=deepcopy(case))
