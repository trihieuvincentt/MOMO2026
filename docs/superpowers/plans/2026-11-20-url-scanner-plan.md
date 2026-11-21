# URL Scanner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Parse submitted URLs safely and report reputation status without implying an unverified URL is safe.

**Architecture:** A pure parser/normalizer produces URL observations; an injected reputation adapter performs a bounded lookup. The service never downloads the submitted page or follows redirects. Structured URL results are passed to the Gemini Investigation Engine for grounded explanation and cross-evidence interpretation; Gemini cannot invent reputation results.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, pytest; selected trusted reputation provider adapter (provider choice gated).

**Spec:** `../specs/2026-11-20-scamguard-mvp-design.md`, Section 7

## Global Constraints

- Never fetch arbitrary user URLs from the app server.
- Reject unsupported schemes and malformed input.
- `no_signal_found` is not a safety guarantee.
- Clearly differentiate live, fixture, unavailable, and error results.
- API credentials remain server-side.

## Review Focus

- `file:`, `javascript:`, or other unsupported schemes: reject.
- localhost/private/link-local IP hostnames: do not issue reputation network requests; return unverified/rejected per policy.
- IDN/punycode and unusual encoding: preserve safe normalized host and mark limitations; never misrepresent as verified.
- Reputation provider timeout/quota: explicit unavailable/error status.
- No reputation match: state only no known match from queried source, not safe.

---

### Task 1: URL parsing and canonical observations

**Files:** `backend/app/schemas/url.py`, `backend/app/services/url_scanner.py`, `backend/tests/test_url_parser.py`

**Interfaces:** `URLScanRequest(url: str)`; `URLObservation(normalized_url: str, hostname: str, scheme: str, notes: list[str])`; `parse_submitted_url(raw: str) -> URLObservation`.

- [ ] Test valid HTTP/HTTPS, malformed strings, unsupported schemes, credentials in URL, localhost/private IP, IDN/punycode, and length limit.
- [ ] Run focused tests; verify they fail.
- [ ] Implement strict parser and normalization; do not resolve or connect to host.
- [ ] Run `pytest backend/tests/test_url_parser.py -q`; expect pass.
- [ ] Commit `feat: parse submitted URLs safely`.

### Task 2: Reputation adapter and service result

**Files:** `backend/app/adapters/reputation.py`, `backend/app/services/url_scanner.py`, `backend/tests/test_reputation_adapter.py`, `backend/tests/test_url_scanner.py`

**Interfaces:** `ReputationProvider.lookup(url: str) -> ReputationLookup`; `scan_url(raw: str, provider: ReputationProvider | None, fixture_mode: bool = False) -> URLScanResult`.

- [ ] Test verified match, no match, timeout, provider error, unconfigured provider, and labeled fixture result.
- [ ] Implement provider interface and map outcomes to verification/status enums; ensure no page-fetch code path exists.
- [ ] Ensure provider receives only validated normalized URLs and local/private targets are not queried.
- [ ] Run focused tests; expect pass.
- [ ] Commit `feat: add URL reputation lookup adapter`.

### Task 3: API and user-facing status semantics

**Files:** `backend/app/api/routes/url.py`, `backend/app/main.py`, `backend/tests/api/test_url_route.py`

**Interfaces:** `POST /api/v1/url/analyze` accepts `URLScanRequest`, returns `URLScanResult` with observation, findings, lookup source/mode, and status.

- [ ] Test invalid URL, live success, fixture mode, and provider outage response.
- [ ] Implement endpoint with explicit `live`, `fixture`, `unavailable`, or `error` mode.
- [ ] Run focused and full backend tests; expect pass.
- [ ] Commit `feat: expose URL assessment endpoint`.
