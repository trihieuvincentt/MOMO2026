# AI Security Advisor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Answer case-related safety questions using actual case findings and curated guidance, while clearly identifying uncertainty and source support.

**Architecture:** Advisor service fetches case context and retrieves a small curated knowledge corpus; Gemini generates a constrained answer with source IDs. Backend validates citations against retrieved passages. Tool calls are limited to implemented backend capabilities.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, pytest; Gemini API adapter; simple keyword retrieval first, optional embeddings/Qdrant only if approved and time permits.

**Spec:** `D:\MOMO2026\scamguard-mvp-spec.md`, Section 11

## Global Constraints

- Gemini cannot claim account, identity, or URL checks unless the relevant tool actually ran.
- User prompts and retrieved documents are untrusted data, not system instructions.
- Cite only retrieved sources with preserved title/publisher/URL.
- Weak retrieval is stated; no fabricated citation.
- Do not request or repeat OTP/password/recovery code/full payment credentials.
- Provider failure returns explicit status and safe fallback.

## Review Focus

- Question asks whether an unverified person is criminal: refuse accusation and explain evidence limits.
- Prompt includes OTP/password: redact/avoid repeating and advise protective action.
- No/weak retrieval: state source limitation; do not invent a source.
- User content or retrieved chunk includes prompt injection: ignore as instructions.
- Gemini claims tool verification not performed: reject or correct the claim.

---

### Task 1: Curate knowledge and implement retrieval contract

**Files:** `backend/app/schemas/knowledge.py`, `backend/app/services/knowledge_retriever.py`, `data/knowledge/`, `backend/tests/test_knowledge_retriever.py`.

**Interfaces:** `KnowledgeSource(title, publisher, url, retrieved_at)`; `KnowledgeChunk(id, text, source)`; `retrieve_guidance(question: str, limit: int = 4) -> list[KnowledgeChunk]`.

- [ ] Add only reviewed official/authoritative safety guidance; preserve publisher, URL, retrieval date.
- [ ] Test relevant retrieval, no-match/weak retrieval, source metadata, and injection-like chunk treated as data.
- [ ] Implement simple keyword retrieval as MVP baseline; keep interface replaceable by vector retrieval.
- [ ] Run focused tests; expect pass.
- [ ] Commit `feat: add curated safety guidance retrieval`.

### Task 2: Implement Advisor prompt/service and Gemini adapter

**Files:** `backend/app/schemas/advisor.py`, `backend/app/adapters/gemini.py`, `backend/app/services/advisor.py`, `backend/tests/test_advisor.py`.

**Interfaces:** `ask_advisor(question: str, case: Case, retriever: KnowledgeRetriever, model: AdvisorModel) -> AdvisorResponse`; response includes answer, cited source IDs, case finding IDs, limitations, status.

- [ ] Test grounded answer/citation, weak retrieval, unverified-person accusation, sensitive credentials, injection, model timeout, and unsupported claim of performed check.
- [ ] Implement constrained prompt with separate untrusted case/evidence/source blocks; pass only real tool outputs and relevant case context.
- [ ] Validate citation IDs against retrieval results and finding references against case; strip/reject unsupported claims.
- [ ] Return safe fallback on provider error; never invent verification status.
- [ ] Run tests; expect pass with mocked model.
- [ ] Commit `feat: add case-grounded security advisor`.

### Task 3: Expose Advisor API and UI

**Files:** `backend/app/api/routes/advisor.py`, `backend/tests/api/test_advisor_route.py`, `frontend/src/features/advisor/AdvisorPanel.tsx`, `frontend/src/features/advisor/AdvisorPanel.test.tsx`.

**Interfaces:** `POST /api/v1/cases/{case_id}/advisor` accepts question; returns `AdvisorResponse`.

- [ ] Test valid case question, unknown case, empty/oversized question, and service unavailable status.
- [ ] Implement endpoint and UI displaying citations/limitations separately from answer.
- [ ] Run focused backend/frontend tests; expect pass.
- [ ] Commit `feat: expose case-aware advisor`.
