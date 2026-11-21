# Message Scanner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Analyze user-provided Vietnamese/English message text and return validated, evidence-linked scam indicators.

**Architecture:** FastAPI route validates input, scanner service applies deterministic checks and calls Gemini through an adapter, and Pydantic validates output. Message findings become structured evidence for the Gemini Investigation Engine; model output is treated as a hypothesis and exact excerpts must map back to input.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, pytest; Gemini API through server-side adapter.

**Spec:** `../specs/2026-11-20-scamguard-mvp-design.md`, Section 6

## Global Constraints

- LLM findings are not externally verified matches.
- Every content finding cites an exact input excerpt.
- No numeric probability; no criminality/identity claims.
- Credentials remain server-side; raw evidence is not logged.
- Provider failure is explicit and does not fabricate findings.

## Review Focus

- Benign urgent language: urgency alone must not force high-risk classification.
- OTP/password included in input: avoid echoing sensitive value and return safe next step.
- Gemini malformed JSON or invalid enum: reject safely with explicit status.
- Gemini invented excerpt: discard unsupported finding.
- Empty/oversized text: return validation error before provider call.

---

### Task 1: Define scanner contracts and deterministic baseline

**Files:** `backend/app/schemas/finding.py`, `backend/app/schemas/message.py`, `backend/app/services/message_scanner.py`, `backend/tests/test_message_scanner.py`

**Interfaces:** `MessageScanRequest(text: str, language_hint: str | None)`; `MessageScanResult(summary: str, findings: list[Finding], limitations: list[str], status: ScannerStatus)`; `analyze_message(request: MessageScanRequest) -> MessageScanResult`.

- [ ] Add tests for empty/oversized input, benign urgency, advance-fee phrase, explicit credential request, and evidence excerpt containment.
- [ ] Run `pytest backend/tests/test_message_scanner.py -q`; verify new tests fail.
- [ ] Implement request limits and a small explainable rule baseline; each rule result includes source `rule` and exact excerpt.
- [ ] Re-run tests; expect all pass without Gemini credentials.
- [ ] Commit `feat: add message scanner baseline`.

### Task 2: Add Gemini adapter and validated model findings

**Files:** `backend/app/adapters/gemini.py`, `backend/app/services/message_scanner.py`, `backend/tests/test_gemini_adapter.py`, `backend/tests/test_message_scanner.py`

**Interfaces:** `GeminiMessageAnalyzer.analyze(text: str, language_hint: str | None) -> MessageModelOutput`; injected adapter, no provider call from route.

- [ ] Test valid structured result, timeout, quota/error, malformed JSON, invalid enum, invented excerpt, and credential redaction.
- [ ] Run tests and verify failures before implementation.
- [ ] Implement provider adapter using server-side configuration and timeout; validate output and retain only findings with input-grounded excerpts.
- [ ] On unavailable provider, return explicit degraded status and deterministic findings only.
- [ ] Run `pytest backend/tests/test_gemini_adapter.py backend/tests/test_message_scanner.py -q`; expect pass.
- [ ] Commit `feat: add grounded Gemini message analysis`.

### Task 3: Expose API and verify request behavior

**Files:** `backend/app/api/routes/message.py`, `backend/app/main.py`, `backend/tests/api/test_message_route.py`

**Interfaces:** `POST /api/v1/message/analyze` accepts `MessageScanRequest`, returns `MessageScanResult`.

- [ ] Test valid Vietnamese/English requests, invalid body/length, provider unavailable, and that response excerpts originate in request text.
- [ ] Implement route mapping validation errors to 4xx and scanner/provider states to explicit response fields.
- [ ] Run focused tests and full backend test suite; expected pass.
- [ ] Commit `feat: expose message analysis endpoint`.
