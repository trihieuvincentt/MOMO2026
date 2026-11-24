# Campaign Intelligence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add deterministic artifact extraction and prior-case campaign matching to ScamGuard reports.

**Architecture:** Artifacts are extracted from message/OCR evidence into the Case JSON payload. A repository extension lists prior cases, a matcher computes safe normalized intersections, and report building exposes supported artifacts and campaign matches. Gemini remains an interpreter, not the source of campaign counts.

**Tech Stack:** Python, Pydantic v2, pytest, existing in-memory/PostgreSQL repositories.

**Spec:** `docs/superpowers/specs/2026-11-24-campaign-intelligence-design.md`

## Global Constraints

- Never invent prior-case counts, campaign names, or matches.
- Do not store API keys, image bytes, passwords, OTPs, or raw credential values in artifacts.
- Preserve `source_evidence_id` on every artifact.
- A match requires two shared artifacts, or one exact URL/phone artifact.
- Preserve existing API behavior and in-memory test isolation.

## Review Focus

- Same text appears twice in one case: deduplicate artifacts and do not count the case twice.
- A prior case contains a matching phrase but no valid source evidence: exclude unsupported artifact.
- URL case/hostname normalization differs: match normalized values without exposing raw unrelated content.
- A case with no prior matches: report an explicit empty match set, not a fabricated campaign.
- Existing Neon payloads lack `artifacts`: load them with an empty default.

---

### Task 1: Artifact schemas and deterministic extraction

**Files:**
- Create: `backend/app/schemas/artifact.py`
- Create: `backend/app/services/artifact_extractor.py`
- Modify: `backend/app/schemas/case.py`
- Test: `backend/tests/test_artifact_extractor.py`

**Interfaces:**
- `ScamArtifact(type, normalized_value, display_value, source_evidence_id, confidence)`.
- `extract_artifacts(evidence: list[EvidenceItem]) -> list[ScamArtifact]`.

- [ ] Write tests for Vietnamese prize text, URL normalization, phone extraction, deduplication, and no credential-value extraction.
- [ ] Run `uv run pytest backend/tests/test_artifact_extractor.py -q`; expect failure because types/functions do not exist.
- [ ] Implement bounded regex extraction for brand, URL, phone, amount, distinctive phrase, and scam pattern; deduplicate by `(type, normalized_value, source_evidence_id)`.
- [ ] Add `artifacts: list[ScamArtifact] = Field(default_factory=list)` to `Case`.
- [ ] Run focused tests; expect pass.
- [ ] Run `uv run pytest -q`; expect all existing tests plus new tests pass.
- [ ] Commit `feat: extract reusable scam artifacts`.

### Task 2: Prior-case repository and campaign matcher

**Files:**
- Modify: `backend/app/services/case_service.py`
- Modify: `backend/app/repositories/case_repository.py`
- Create: `backend/app/services/campaign_matcher.py`
- Test: `backend/tests/test_campaign_matcher.py`

**Interfaces:**
- Repository optional method `list_cases() -> list[Case]` for campaign lookup.
- `CampaignMatch(case_ids: list[str], shared_artifact_types: list[str], shared_artifact_values: list[str], score: int)`.
- `match_campaigns(case: Case, prior_cases: list[Case]) -> list[CampaignMatch]`.

- [ ] Add tests for no match, two-artifact match, exact URL match, same-case exclusion, and unsupported artifact exclusion.
- [ ] Run focused matcher tests; expect failure.
- [ ] Implement `list_cases` for in-memory and PostgreSQL repositories using a bounded query/read path; keep existing `CaseRepository` callers compatible.
- [ ] Implement deterministic matching and the minimum match rule from the spec.
- [ ] Run focused and full tests; expect pass.
- [ ] Commit `feat: match related scam cases`.

### Task 3: Analyze cases and expose campaign intelligence in report

**Files:**
- Modify: `backend/app/services/case_service.py`
- Modify: `backend/app/schemas/report.py`
- Modify: `backend/app/services/report_builder.py`
- Modify: `backend/app/api/routes/cases.py` only if report dependencies require it.
- Test: `backend/tests/test_campaign_integration.py`, `backend/tests/test_report_builder.py`

**Interfaces:**
- `Case.artifacts` is populated before persistence after analysis.
- `InvestigationReport.artifacts` and `InvestigationReport.campaign_matches` are structured lists.

- [ ] Write integration tests creating prior and current cases, analyzing them with deterministic scanners, and asserting artifacts/matches persist and report output is supported.
- [ ] Run tests to verify failure.
- [ ] Populate artifacts after evidence scanning, match against prior cases excluding the current case, and save the case.
- [ ] Add report schemas and deterministic builder fields; include no-match limitation only when appropriate.
- [ ] Run focused and full suite; expect pass.
- [ ] Commit `feat: add campaign intelligence to reports`.

### Task 4: Demo-safe frontend display

**Files:**
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`
- Test: `backend/tests/test_frontend_contract.py`

- [ ] Add contract tests for `artifacts`, `campaign_matches`, shared artifact display, and explicit no-match copy.
- [ ] Run to verify failure.
- [ ] Render normalized artifacts and campaign matches safely with escaped text; never display unrelated raw case content.
- [ ] Run full suite and commit `feat: show campaign intelligence in judge UI`.

### Task 5: Deployment verification

- [ ] Run `uv run pytest -q`.
- [ ] Deploy the branch to Render.
- [ ] Create two synthetic cases using the same safe prize text; verify the second report shows a real match count of 1 and shared artifacts.
- [ ] Verify a single case reports no campaign match and does not claim safety.
- [ ] Document only observed results; never use fabricated demo counts.
