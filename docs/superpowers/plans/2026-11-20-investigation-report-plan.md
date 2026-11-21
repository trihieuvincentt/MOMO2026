# Investigation Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Render a readable investigation report that explains risk, evidence, verification, unknowns, and next actions.

**Architecture:** A report builder transforms the canonical Case, RiskAssessment, and Recommendations into a stable response model. Frontend renders structured sections; it does not parse raw LLM text to infer facts.

**Tech Stack:** FastAPI, Pydantic, pytest; React/TypeScript, Vitest.

**Spec:** `../specs/2026-11-20-scamguard-mvp-design.md`, Section 12

## Global Constraints

- Every report statement traces to a finding, input, or knowledge source.
- Failed/unavailable checks are visible.
- Neutral language; no unsupported certainty or uncalibrated probability.
- “No known signal found” is explicitly not a guarantee of safety.
- Report remains useful when a scanner fails.

## Review Focus

- Partial scanner failure: show unavailable check and successful results together.
- Finding without evidence/source: do not render as supported fact.
- No-known-signal category: show safety limitation prominently.
- Long evidence excerpt: constrain presentation while allowing source inspection.
- Empty case or malformed report payload: show helpful empty/error state, not a misleading report.

---

### Task 1: Define report contract and builder

**Files:** `backend/app/schemas/report.py`, `backend/app/services/report_builder.py`, `backend/tests/test_report_builder.py`.

**Interfaces:** `build_report(case: Case, risk: RiskAssessment, recommendations: list[Recommendation]) -> InvestigationReport`; sections include summary, evidence items, findings, supported relationships, unknowns/limitations, actions.

- [x] Test full case, partial scanner failure, no-known-signal, unsupported finding, empty case, and evidence references.
- [x] Implement builder as deterministic transformation; exclude unsupported statements and include statuses/limitations.
- [x] Run report builder tests; expect pass.
- [x] Commit `feat: build structured investigation reports`.

### Task 2: Expose report endpoint

**Files:** `backend/app/api/routes/cases.py`, `backend/tests/api/test_report_route.py`.

**Interfaces:** `GET /api/v1/cases/{case_id}/report` returns `InvestigationReport`.

- [x] Test existing case, missing case, scanner unavailable, and response schema validation.
- [x] Implement endpoint by loading canonical case and invoking report builder.
- [x] Run focused and backend tests; expect pass.
- [x] Commit `feat: expose investigation report endpoint`.

### Task 3: Render report UI and verify traceability

**Files:** `frontend/src/features/report/InvestigationReport.tsx`, `frontend/src/features/report/InvestigationReport.test.tsx`, `frontend/src/components/{FindingCard,StatusBadge,ErrorNotice}.tsx`.

- [ ] Test each required section, source/evidence labels, failure status, and no-signal disclaimer.
- [ ] Implement sectioned report rendering with accessible status text and safe excerpt display.
- [ ] Test report remains understandable with partial results and can navigate findings to evidence item.
- [ ] Run frontend tests and end-to-end flow tests; expect pass.
- [ ] Commit `feat: render explainable investigation report`.
