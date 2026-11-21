from dataclasses import dataclass

from backend.app.schemas.case import CaseStatus, EvidenceScanStatus
from backend.app.schemas.evidence import EvidenceType
from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.message import MessageScanResult, ScannerStatus
from backend.app.schemas.url import URLScanResult, URLObservation, URLResultMode, URLScanStatus
from backend.app.services.case_service import (
    InMemoryCaseRepository,
    ScannerRegistry,
    add_evidence,
    analyze_case,
    create_case,
)


def _finding(category: str) -> Finding:
    return Finding(
        id=f"finding-{category}",
        category=category,
        description="test finding",
        source_type=FindingSource.RULE,
        verification_status=VerificationStatus.SUSPICIOUS_INDICATOR,
        severity=Severity.MEDIUM,
    )


def _url_result() -> URLScanResult:
    return URLScanResult(
        observation=URLObservation(
            normalized_url="https://example.com/",
            hostname="example.com",
            scheme="https",
        ),
        findings=[_finding("url_signal")],
        limitations=[],
        status=URLScanStatus.SUCCESS,
        mode=URLResultMode.LIVE,
        lookup_source="test",
    )


def test_analyze_case_preserves_message_and_url_findings_with_provenance():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    message = add_evidence(repository, case.id, EvidenceType.MESSAGE, "Pay a verification fee")
    url = add_evidence(repository, case.id, EvidenceType.URL, "https://example.com/")

    scanners = ScannerRegistry(
        message=lambda text: MessageScanResult(
            summary="message result",
            findings=[_finding("message_signal")],
            limitations=[],
            status=ScannerStatus.SUCCESS,
        ),
        url=lambda value: _url_result(),
    )

    result = analyze_case(repository, case.id, scanners)

    assert result.case.status == CaseStatus.ANALYZED
    assert result.case.scanner_statuses[message.id] == EvidenceScanStatus.SUCCESS
    assert result.case.scanner_statuses[url.id] == EvidenceScanStatus.SUCCESS
    assert {finding.evidence_item_id for finding in result.case.findings} == {message.id, url.id}


def test_ocr_text_is_sent_to_message_scanner_only_after_it_is_evidence():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    ocr = add_evidence(repository, case.id, EvidenceType.OCR_TEXT, "Your account is locked")
    seen: list[str] = []

    def scan_message(text: str) -> MessageScanResult:
        seen.append(text)
        return MessageScanResult(summary="ok", findings=[], limitations=[], status=ScannerStatus.SUCCESS)

    result = analyze_case(repository, case.id, ScannerRegistry(message=scan_message))

    assert seen == ["Your account is locked"]
    assert result.case.scanner_statuses[ocr.id] == EvidenceScanStatus.SUCCESS


def test_failed_url_scan_preserves_successful_message_and_marks_url_error():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    message = add_evidence(repository, case.id, EvidenceType.MESSAGE, "Hello")
    url = add_evidence(repository, case.id, EvidenceType.URL, "https://example.com/")

    def failing_url(value: str) -> URLScanResult:
        raise TimeoutError("provider timeout")

    result = analyze_case(
        repository,
        case.id,
        ScannerRegistry(
            message=lambda text: MessageScanResult(summary="ok", findings=[], limitations=[], status=ScannerStatus.SUCCESS),
            url=failing_url,
        ),
    )

    assert result.case.scanner_statuses[message.id] == EvidenceScanStatus.SUCCESS
    assert result.case.scanner_statuses[url.id] == EvidenceScanStatus.UNAVAILABLE
    assert result.case.status == CaseStatus.ANALYZED


def test_exact_shared_url_gets_explicit_relationship_but_unrelated_items_do_not():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    add_evidence(repository, case.id, EvidenceType.MESSAGE, "Review https://example.com/ now")
    add_evidence(repository, case.id, EvidenceType.URL, "https://example.com/")
    add_evidence(repository, case.id, EvidenceType.URL, "https://other.example/")

    result = analyze_case(repository, case.id, ScannerRegistry())

    assert len(result.case.relationships) == 1
    assert "exact URL" in result.case.relationships[0].basis
