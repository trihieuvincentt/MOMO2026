# Investigation Case Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Group message, URL, and screenshot-derived evidence into a case while preserving each scanner's provenance and partial results.

**Architecture:** A case service owns evidence lifecycle and scanner orchestration. Evidence and findings are linked by identifiers; a relationship is recorded only with explicit support. Persistence is optional for MVP and must be decided before deployment.

**Tech Stack:** FastAPI, Pydantic, pytest; PostgreSQL only if persistent case history is selected; React/TypeScript.

**Spec:** `D:\MOMO2026\scamguard-mvp-spec.md`, Section 9

## Global Constraints

- Every finding references an evidence item or declares case-level scope and rationale.
- Co-submission alone does not prove evidence is related.
- Partial scanner failure preserves successful results and exposes failed status.
- Case IDs must not encode secrets/personal data.
- Session-scoped mode is acceptable for MVP unless persistence is approved.

## Review Focus

- Two unrelated inputs in one case: no relationship inferred.
- Same URL appears exactly in message and URL item: link only with recorded basis.
- One scanner fails: preserve other findings and per-item error status.
- Duplicate submission: avoid accidental duplicate item or document duplicate semantics.
- Unknown/malformed case ID: return safe not-found/validation response without leaking another case.

---

### Task 1: Define case/evidence contracts and service

**Files:** `backend/app/schemas/case.py`, `backend/app/services/case_service.py`, `backend/tests/test_case_service.py`.

**Interfaces:** `create_case() -> Case`; `add_evidence(case_id: str, item: EvidenceItemInput) -> EvidenceItem`; `get_case(case_id: str) -> Case`; `Case` includes evidence, findings, scanner statuses, and supported relationships.

- [ ] Test create, add evidence, invalid case, duplicate policy, provenance links, and unrelated evidence.
- [ ] Implement in-memory repository for first testable vertical slice and explicit repository interface.
- [ ] Run case service tests; expect pass.
- [ ] Commit `feat: model investigation cases and evidence`.

### Task 2: Orchestrate scanners with partial-failure behavior

**Files:** `backend/app/services/case_service.py`, `backend/tests/test_case_orchestration.py`.

**Interfaces:** `analyze_case(case_id: str, scanners: ScannerRegistry) -> CaseAnalysisResult`; registry returns typed per-evidence result/status.

- [ ] Test message+URL analysis, OCR-confirmed text association, scanner timeout/error, and no unsupported correlation.
- [ ] Implement orchestration with injected scanners; persist each successful result and explicit status independently.
- [ ] Add only deterministic links supported by exact shared value or explicit user relationship; record link basis.
- [ ] Run case tests; expect pass.
- [ ] Commit `feat: orchestrate case evidence analysis`.

### Task 3: API and optional persistence boundary

**Files:** `backend/app/api/routes/cases.py`, `backend/app/repositories/case_repository.py`, `backend/tests/api/test_case_routes.py`.

**Interfaces:** `POST /api/v1/cases`, `POST /api/v1/cases/{case_id}/evidence`, `POST /api/v1/cases/{case_id}/analyze`, `GET /api/v1/cases/{case_id}`.

- [ ] Test valid lifecycle, invalid IDs/payloads, partial failures, and isolation between generated case IDs.
- [ ] Implement route layer over repository interface; default in-memory mode unless persistent store selected.
- [ ] If PostgreSQL chosen, add migration and repository integration tests; otherwise document restart/session limitation.
- [ ] Run API and full backend tests; expect pass.
- [ ] Commit `feat: expose investigation case workflow`.
