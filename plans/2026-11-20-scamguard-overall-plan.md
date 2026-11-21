# ScamGuard MVP — Overall Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the ScamGuard seven-capability MVP as a safe, repeatable end-to-end investigation workflow.

**Architecture:** React/TypeScript frontend calls a Python/FastAPI backend. Backend owns validation, OCR, scanner orchestration, deterministic risk aggregation, report assembly, Gemini calls, reputation-provider integration, and optional persistence/RAG. Shared Pydantic contracts preserve evidence provenance from ingestion through report. No arbitrary URL fetching is permitted.

**Tech Stack:** Proposed baseline: Python 3.12+, FastAPI, Pydantic, pytest; React + TypeScript + Vite, Vitest; PaddleOCR (proof-of-fit required); Gemini API behind adapter; PostgreSQL/Qdrant optional. Confirm versions, deployment target, and provider availability before implementation.

**Spec:** `D:\MOMO2026\scamguard-mvp-spec.md`

## Global Constraints

- Findings include source type, verification status, severity, and evidence reference/excerpt.
- LLM-generated findings are hypotheses, not externally verified matches.
- Do not present an unvalidated numeric scam probability.
- No arbitrary URL page fetching from the application server.
- Provider keys remain backend-only; never expose them in frontend code.
- No OTP/password/recovery code requests; avoid logging raw evidence.
- Fixtures must be visibly labeled as demo/test data, never live lookup results.
- OCR text is user-reviewable before analysis; allow manual-text fallback.
- Scanner failures remain explicit and must not erase other successful results.
- “No known signal found” is not a guarantee of safety.

## Review Focus

- URL pointing to localhost/private/link-local IP or unusual scheme: reject safely without making a network request (URL plan test).
- Image with valid extension but non-image bytes, or oversized dimensions: reject and clean temporary data (OCR plan test).
- Gemini returns malformed JSON, invented excerpt, or instruction-following output: validate/reject and preserve safe error status (Message/Advisor plan tests).
- Corrupt or partial case submission with one downstream provider failure: retain successful evidence and expose failed status (Case/Report plan tests).
- Evidence items are unrelated but submitted together: do not imply a relationship or elevate risk from association alone (Case/Risk plan tests).

---

## Delivery sequence

The individual plans are independently testable; execute in this dependency order:

1. **Foundation and shared contracts** — create backend/frontend skeleton, configuration, schemas, health route, test harness. This is a prerequisite task in this plan, not a separate feature plan.
2. **Message Scanner** — establish normalized Finding and scanner contracts.
3. **URL Scanner** — implement parsing and reputation adapter without fetching submitted pages.
4. **Screenshot OCR** — run PaddleOCR proof-of-fit; expose editable extraction flow.
5. **Investigation Case** — aggregate evidence and scanner outputs, preserving provenance.
6. **Explainable Risk Assessment** — deterministic policy over validated findings.
7. **Investigation Report** — user-facing report from case, risk, and recommendation contracts.
8. **AI Security Advisor** — case-grounded Q&A and curated guidance retrieval, after case/report contracts stabilize.
9. **End-to-end hardening and demo** — regression/evaluation set, fixture labeling, deployment, privacy checks, rehearsed demo and recorded backup.

## Proposed repository structure

```text
backend/app/
  main.py
  api/routes/{health,message,url,ocr,cases,advisor}.py
  core/{config,errors}.py
  schemas/{evidence,finding,case,report,advisor}.py
  services/{message_scanner,url_scanner,ocr,case_service,risk_assessor,report_builder,advisor}.py
  adapters/{gemini,reputation,ocr_engine,knowledge_retriever}.py
frontend/src/
  api/client.ts
  features/{investigation,message,url,ocr,report,advisor}/
  components/{FindingCard,StatusBadge,ErrorNotice}.tsx
  types/contracts.ts
tests/backend/
frontend/src/**/*.test.ts(x)
data/evaluation/
```

## Tasks

### Task 1: Establish shared contracts and application skeleton

**Files:** Create `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/schemas/{evidence,finding,case}.py`, `backend/app/api/routes/health.py`, `backend/tests/test_health.py`, `backend/tests/test_contracts.py`, `frontend/src/types/contracts.ts`, `frontend/src/api/client.ts`.

**Interfaces:**
- Produces Pydantic models `EvidenceItem`, `Finding`, `ScannerStatus`, `Case`; frontend matching TypeScript types.
- `Finding.verification_status` is one of `verified_match`, `suspicious_indicator`, `unverified`, `no_signal_found`; scanner status separately represents `success`, `unavailable`, `error`.

- [ ] Test health endpoint and reject invalid status/enum values.
- [ ] Run tests and confirm they fail before implementation.
- [ ] Implement app factory/config and schemas; no secrets committed, configuration read from environment.
- [ ] Run `pytest backend/tests -q`; expected all foundation tests pass.
- [ ] Commit `feat: establish shared application contracts`.

### Task 2: Implement the seven feature plans

Execute the seven linked plans in the order above, preserving their interfaces and acceptance tests. Each feature plan ends with a testable deliverable and commit. Do not start a downstream integration before its upstream contract exists.

### Task 3: Integrate the investigation journey

**Files:** Create `backend/app/api/routes/cases.py`, `backend/tests/integration/test_investigation_flow.py`, `frontend/src/features/investigation/InvestigationPage.tsx`, `frontend/src/features/investigation/InvestigationPage.test.tsx`.

**Interfaces:** Consumes scanner, OCR, case, risk, report, and Advisor interfaces from individual plans. Produces one user workflow: create case → add evidence → review OCR → analyze → report → ask follow-up.

- [ ] Write integration tests for message+URL case, screenshot review flow, and partial provider failure.
- [ ] Verify test failures identify missing integration behavior.
- [ ] Wire services via case orchestration; return per-item statuses and preserve completed results on partial failure.
- [ ] Run `pytest backend/tests -q` and frontend test command; expected pass.
- [ ] Commit `feat: integrate investigation workflow`.

### Task 4: Build evaluation fixtures and verify safety behavior

**Files:** Create `data/evaluation/cases.jsonl`, `backend/tests/evaluation/test_evaluation_cases.py`, `docs/demo-runbook.md`.

- [ ] Add de-identified/synthetic benign, suspicious, ambiguous, malformed URL, provider outage, low-quality OCR, unrelated-evidence, and credential-exposure cases.
- [ ] Test that fixtures are labeled and never returned as live lookup.
- [ ] Run evaluation and record per-case outcomes, false positives/negatives, and limitations; do not claim statistical representativeness.
- [ ] Commit `test: add scamguard evaluation fixtures`.

### Task 5: Operational readiness and demo

**Files:** Modify deployment configuration and README; create `.env.example` without secrets, `docs/privacy-and-retention.md`, `docs/demo-runbook.md`.

- [ ] Verify app starts with external providers disabled and shows unavailable states.
- [ ] Verify configured providers use server-side credentials and timeouts.
- [ ] Run complete demo twice, once with live services if available and once with deterministic labeled fixtures.
- [ ] Confirm temporary image cleanup, redacted logs, known limitations, and backup recording.
- [ ] Commit `docs: prepare reproducible contest demo`.

## Feature plans

- Message Scanner: `D:\MOMO2026\plans\2026-11-20-message-scanner-plan.md`
- URL Scanner: `D:\MOMO2026\plans\2026-11-20-url-scanner-plan.md`
- Screenshot OCR: `D:\MOMO2026\plans\2026-11-20-screenshot-ocr-plan.md`
- Investigation Case: `D:\MOMO2026\plans\2026-11-20-investigation-case-plan.md`
- Explainable Risk Assessment: `D:\MOMO2026\plans\2026-11-20-risk-assessment-plan.md`
- AI Security Advisor: `D:\MOMO2026\plans\2026-11-20-ai-security-advisor-plan.md`
- Investigation Report: `D:\MOMO2026\plans\2026-11-20-investigation-report-plan.md`

## Self-review

Coverage: all seven spec sections map to feature plans; shared privacy/security constraints map to foundation and operational-readiness tasks. Interfaces are shared through Pydantic/TypeScript contracts and the `Finding` provenance model. Review-focus tests are assigned to the owning feature. This is a proposed greenfield structure because the supplied folder contains the plan/spec documents, not an application repository; revise file paths to match the actual repository before execution. External provider, persistence, and deployment choices remain gated decisions, not assumed facts.
