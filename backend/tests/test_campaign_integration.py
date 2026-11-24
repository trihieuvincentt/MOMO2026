from backend.app.schemas.case import Case
from backend.app.schemas.evidence import EvidenceItem, EvidenceType
from backend.app.services.case_service import InMemoryCaseRepository, ScannerRegistry, add_evidence, analyze_case, create_case


def test_analysis_persists_artifacts_and_prior_case_match():
    repository = InMemoryCaseRepository()
    prior = create_case(repository)
    add_evidence(
        repository,
        prior.id,
        EvidenceType.MESSAGE,
        "Chúc mừng Facebook trúng giải nhất, phiếu quà tặng 55.000.000 VNĐ, mã số may mắn.",
    )
    analyze_case(repository, prior.id, ScannerRegistry(message=lambda text: type("Result", (), {"status": "success", "findings": []})()))

    current = create_case(repository)
    add_evidence(
        repository,
        current.id,
        EvidenceType.MESSAGE,
        "Chúc mừng Facebook trúng giải nhất, phiếu quà tặng 55.000.000 VNĐ, mã số may mắn.",
    )
    analyzed = analyze_case(repository, current.id, ScannerRegistry(message=lambda text: type("Result", (), {"status": "success", "findings": []})())).case

    assert analyzed.artifacts
    assert analyzed.campaign_matches
    assert prior.id in analyzed.campaign_matches[0].case_ids
    assert repository.get(current.id).artifacts
