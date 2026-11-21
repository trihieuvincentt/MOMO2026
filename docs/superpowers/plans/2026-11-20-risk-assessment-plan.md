# Explainable Risk Assessment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert validated structured findings into a reproducible risk category with evidence, uncertainty, and safe actions.

**Architecture:** Pure deterministic policy evaluates findings; each category outcome carries contributing finding IDs, missing checks, and rationale. No LLM score or numeric probability.

**Tech Stack:** Python 3.12+, Pydantic, pytest.

**Spec:** `../specs/2026-11-20-scamguard-mvp-design.md`, Section 10

## Global Constraints

- Categories: `high_risk`, `elevated_risk`, `caution`, `no_known_signal_found`, `insufficient_information`.
- No calibrated probability or hidden model score.
- Every reason references a validated finding/evidence/source.
- No match is not evidence of safety.
- Risk rules are versioned/documented and deterministic.

## Review Focus

- Verified malicious reputation match: high-risk result with exact source reference.
- Multiple weaker indicators: aggregate only under documented rules.
- Unavailable scanner: assessment reflects missing information.
- No findings and all checks completed: no-known-signal, never safe/low-risk guarantee.
- Contradictory or duplicated findings: avoid accidental double counting and expose uncertainty.

---

### Task 1: Define risk result and rule set

**Files:** `backend/app/schemas/risk.py`, `backend/app/services/risk_assessor.py`, `backend/tests/test_risk_assessor.py`, `docs/risk-policy.md`.

**Interfaces:** `assess_risk(findings: list[Finding], scanner_statuses: list[ScannerStatus]) -> RiskAssessment`; result includes category, explanation, contributing IDs, unknowns, recommendations, and `policy_version`.

- [x] Add table-driven tests for each category, verified match, missing scan, duplicate findings, and contradictions.
- [x] Document initial strong/weak indicator mapping and aggregation thresholds in `docs/risk-policy.md` before implementation.
- [x] Implement pure deterministic policy; do not accept free-form model risk score.
- [x] Run focused tests; expect pass and deterministic outputs.
- [x] Commit `feat: add explainable risk policy`.

### Task 2: Add recommendation mapping and safety copy

**Files:** `backend/app/services/recommendation_catalog.py`, `backend/tests/test_recommendation_catalog.py`, `backend/app/services/risk_assessor.py`.

**Interfaces:** `recommend_actions(assessment: RiskAssessment, findings: list[Finding]) -> list[Recommendation]`.

- [x] Test high/elevated/caution/no-signal/insufficient-information actions, including before-payment and credential-exposure cases.
- [x] Implement curated action templates; do not ask for credentials or imply transfer blocking.
- [x] Ensure every recommendation includes reason and priority.
- [x] Run tests; expect pass.
- [x] Commit `feat: map risk findings to safe actions`.

### Task 3: Expose assessment contract for case integration

**Files:** `backend/app/services/case_service.py`, `backend/tests/test_risk_integration.py`.

- [x] Test that only validated findings contribute, unavailable checks produce unknowns, and reportable evidence references survive aggregation.
- [x] Integrate the pure assessor into case analysis; retain policy version in result.
- [x] Run risk and case integration suites; expect pass.
- [x] Commit `feat: integrate risk assessment with cases`.
