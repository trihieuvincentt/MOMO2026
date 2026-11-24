from backend.app.schemas.case import Case
from backend.app.schemas.artifact import ArtifactType, CampaignMatch


def _supported_artifacts(case: Case):
    evidence_ids = {item.id for item in case.evidence}
    return {
        (artifact.type.value, artifact.normalized_value): artifact
        for artifact in case.artifacts
        if artifact.source_evidence_id in evidence_ids
    }


def match_campaigns(case: Case, prior_cases: list[Case]) -> list[CampaignMatch]:
    current = _supported_artifacts(case)
    matches: list[CampaignMatch] = []
    for prior in prior_cases:
        if prior.id == case.id:
            continue
        shared = sorted(set(current) & set(_supported_artifacts(prior)))
        if not shared:
            continue
        shared_types = sorted({kind for kind, _ in shared})
        exact_artifact = any(kind in {ArtifactType.URL.value, ArtifactType.PHONE.value} for kind, _ in shared)
        if len(shared) < 2 and not exact_artifact:
            continue
        matches.append(
            CampaignMatch(
                case_ids=[prior.id],
                shared_artifact_types=shared_types,
                shared_artifact_values=[value for _, value in shared],
                score=len(shared),
            )
        )
    return matches
