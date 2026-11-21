import pytest

from backend.app.schemas.case import CaseStatus
from backend.app.schemas.evidence import EvidenceType
from backend.app.services.case_service import (
    DuplicateEvidenceError,
    InMemoryCaseRepository,
    add_evidence,
    create_case,
    get_case,
)


def test_create_case_uses_opaque_id_and_starts_open():
    repository = InMemoryCaseRepository()

    case = create_case(repository)

    assert case.id.startswith("case-")
    assert case.status == CaseStatus.OPEN
    assert case.evidence == []


def test_add_evidence_preserves_type_and_content_reference():
    repository = InMemoryCaseRepository()
    case = create_case(repository)

    item = add_evidence(repository, case.id, EvidenceType.MESSAGE, "Please pay a fee")

    stored = get_case(repository, case.id)
    assert item.type == EvidenceType.MESSAGE
    assert item.content_reference == "Please pay a fee"
    assert stored.evidence[0].id == item.id


def test_unknown_case_does_not_leak_or_create_data():
    repository = InMemoryCaseRepository()

    with pytest.raises(KeyError):
        get_case(repository, "case-does-not-exist")


def test_duplicate_evidence_is_rejected_for_same_type_and_content():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    add_evidence(repository, case.id, EvidenceType.URL, "https://example.com")

    with pytest.raises(DuplicateEvidenceError):
        add_evidence(repository, case.id, EvidenceType.URL, "https://example.com")


def test_different_evidence_items_do_not_create_relationship_implicitly():
    repository = InMemoryCaseRepository()
    case = create_case(repository)
    add_evidence(repository, case.id, EvidenceType.MESSAGE, "Hello, please pay now")
    add_evidence(repository, case.id, EvidenceType.URL, "https://unrelated.example")

    stored = get_case(repository, case.id)

    assert stored.relationships == []
