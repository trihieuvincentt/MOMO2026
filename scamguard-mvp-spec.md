# ScamGuard AI — Product & Technical Specification

**Status:** Draft for user review — specification only; implementation plan intentionally deferred until approval  
**Source:** `D:\MOMO2026\plan (9).md` and decisions discussed in conversation  
**Date:** 2026-11-20

## 1. Purpose and product intent

ScamGuard AI helps a person assess a suspicious digital interaction before sending money or disclosing sensitive information. It treats a message, URL, and screenshot as evidence items within one investigation rather than isolated classification prompts. The system presents traceable findings, distinguishes verified results from inferred indicators and unknowns, and recommends safe next steps.

The MVP is for a contest demonstration by a small team. Success means a repeatable end-to-end investigation can be demonstrated, including at least two evidence types, with useful explanations and honest limitations. It is not a production fraud-detection authority.

## 2. Product goals

- Accept message text, URLs, and screenshots as evidence.
- Analyze each evidence type with a suitable component.
- Preserve the provenance of every finding and avoid unsupported cross-evidence claims.
- Present an understandable risk category, evidence, uncertainty, limitations, and recommended actions.
- Offer case-aware safety guidance supported by curated knowledge sources where available.
- Handle invalid input and service failures without falsely implying that a check succeeded.
- Minimize exposure and retention of sensitive content.

## 3. Non-goals and anti-goals

### Non-goals for this MVP

- Integration with MoMo, banks, payment rails, or account verification.
- Blocking or reversing payments, or guaranteeing that an item or transaction is safe.
- Fetching arbitrary submitted websites from the main application environment.
- Public reputation scoring or accusations against named people, phone numbers, or account holders.
- Native mobile apps, browser extensions, voice/deepfake analysis, or real-time monitoring.
- Building a large-scale threat-intelligence platform.

### Anti-goals

- Do not present model-generated claims as verified facts.
- Do not label a URL safe merely because no reputation match was found.
- Do not show a numeric probability as calibrated unless it has been validated as such.
- Do not ask for OTPs, passwords, recovery codes, or full payment credentials.
- Do not present fixtures or cached demo data as live external lookups.
- Do not keep raw evidence or credentials in logs unnecessarily.

## 4. Constraints and decisions

### Confirmed from the source plan or conversation

- MVP consists of seven capabilities described in Sections 6–12.
- Gemini is the proposed language-model API for message analysis and Advisor behavior.
- The user chose a separate OCR stage rather than sending the screenshot directly to Gemini. PaddleOCR is the proposed local OCR implementation; Vietnamese and English support must be tested before treating it as a supported guarantee.
- OCR text should be shown for user review/correction before analysis.
- Risk aggregation should be transparent and rule-based, not a model-invented probability.
- URL reputation lookup may use a trusted provider; demo fixtures are acceptable only when clearly labeled.
- The existing source plan suggests React/Next.js, FastAPI, PostgreSQL, and optionally Qdrant, but does not make them final choices.

### Specification defaults proposed for approval

- No user account/authentication is required for the contest MVP unless the competition rules or deployment needs require it.
- A case is scoped to the current browser session or a generated case identifier; durable history is optional and not a core acceptance requirement.
- The backend owns provider credentials and all third-party calls. The frontend never receives API keys.
- The application does not download page content for arbitrary URLs. URL analysis is parsing plus a reputation lookup or a clearly labeled unavailable/fixture result.
- If a provider is not configured or fails, return an explicit `unavailable`/`error` status and continue with other evidence where possible.
- The knowledge base is a small, curated set of safety guidance. Retrieval/vector infrastructure is implementation detail and may be omitted if it endangers the core workflow.
- User-submitted evidence is retained only as long as required for the active case/demo; persistent retention and deployment privacy terms must be decided before public release.

### Unverified constraint

The contest-rules PDF in `D:\MOMO2026` could not be rendered in the available environment. This draft has not been checked against the contest's exact technical, submission, or judging requirements.

## 5. Overall user journey and system behavior

1. User starts a new investigation.
2. User adds a message, URL, screenshot, or combination of these.
3. For screenshots, the system extracts text and lets the user review/edit it before analysis.
4. Each scanner returns structured findings with evidence references, source, and verification state.
5. The investigation service associates findings with evidence items. It may link items only when there is a concrete basis (for example, the submitted message contains the same URL); otherwise it must preserve them as separate items.
6. A deterministic risk policy aggregates supported findings and records which findings contributed.
7. The report displays risk category, findings, evidence, unknowns, limitations, and prioritized next steps.
8. The Advisor answers a follow-up using case findings and retrieved curated guidance; it must not claim checks that were not performed.

### Shared finding contract

Every finding shown to the user should contain:

- `id` and `category`;
- `description` written in clear language;
- `evidence_item_id` (or explicit case-level scope);
- `evidence_excerpt` or source reference when applicable;
- `source_type`: `user_input`, `rule`, `reputation_api`, `ocr`, `llm`, or `knowledge_base`;
- `verification_status`: `verified_match`, `suspicious_indicator`, `unverified`, or `no_signal_found`;
- `severity`: a small documented ordinal such as `low`, `medium`, `high`;
- optional limitations/notes.

Do not treat an LLM-produced finding as an externally verified match. Validate model output against a schema and reject or safely handle malformed output.

## 6. Specification — Message Scanner

### Purpose
Analyze user-provided message text for scam-related indicators and return evidence-linked findings, not a bare scam/not-scam verdict.

### Inputs
- Required: message text, trimmed and within a configured maximum length.
- Optional: locale/language hint and case/evidence identifier.
- The system should support Vietnamese and English content to the extent verified by tests; language detection may be advisory.

### Processing
- Apply deterministic checks for high-value patterns where appropriate (for example, explicit OTP/password requests or advance-fee language).
- Gemini may classify and explain indicators using a constrained structured-output contract.
- The model must cite excerpts that occur in the submitted text. Backend validation must ensure excerpts are substrings or otherwise verifiably aligned to the input.
- Return an explicit uncertainty/limitations field. Do not infer identity, criminality, or intent of a person from text alone.

### Output
- Findings with category, severity, evidence excerpt, source type, and verification status.
- A concise neutral summary and recommended next action(s).
- Processing status and limitations.

### Acceptance criteria
- Valid Vietnamese and English examples return schema-valid results.
- Each content-based finding is traceable to an exact text excerpt or is omitted.
- Benign urgent messages do not automatically become high-risk solely because they sound urgent.
- Empty/oversized/malformed inputs are rejected with actionable errors.
- Gemini timeout, quota, or invalid output produces a clear degraded/error state, not a fabricated analysis.

## 7. Specification — URL Scanner

### Purpose
Assess URL structure and, where configured, query a trusted reputation service while communicating exactly what was and was not checked.

### Inputs
- One URL string, optionally associated with a case/evidence identifier.
- Accept only supported schemes (normally `http`/`https`) and enforce length limits.

### Processing
- Parse and normalize safely; identify malformed input and basic observations (scheme, hostname, unusual encoding or lookalike-like characteristics only if implemented and tested).
- Query an approved reputation provider through the backend when configured.
- Do not retrieve arbitrary page content or follow redirects in the MVP.
- Provider responses must be mapped to `verified_match`, `no_signal_found`, `unverified`, or `unavailable/error` with provider and timestamp metadata as appropriate.
- Fixtures are allowed for deterministic demos only if the response is visibly marked as demo/test data.

### Output
- Parsed hostname and safe URL observations.
- Reputation status, source/provider, check time/status, and limitations.
- Findings must not state that an unlisted URL is safe.

### Acceptance criteria
- Handles valid, malformed, unsupported-scheme, unknown, known fixture, and provider-failure cases.
- Does not fetch submitted URLs from the application server.
- Distinguishes live lookup from fixture and unavailable states in API response and UI.
- Secrets/provider keys remain server-side.

## 8. Specification — Screenshot OCR

### Purpose
Extract text from a user-provided screenshot so the user can inspect/correct it and submit the approved text to the Message Scanner.

### Inputs and validation
- Image upload with a small allowlist of raster formats (for example PNG/JPEG); enforce a configurable byte and pixel limit.
- Validate file signature/content rather than trusting the filename or MIME header alone.
- Reject unsupported, corrupt, empty, or oversized images with a clear message.

### Processing
- Run OCR as a separate backend component, initially PaddleOCR if a proof-of-fit confirms installation, deployment footprint, license, and Vietnamese/English quality.
- Treat language support as tested capability, not an assumption; mixed-language screenshots should be included in validation.
- Return extracted text and, if available, confidence/region data. Do not silently analyze OCR output before the user has had the opportunity to review it.
- Provide a manual text-entry fallback when OCR fails or returns too little text.
- Avoid logging/storing raw images beyond the active workflow unless retention is explicitly approved.

### Output and acceptance criteria
- User can view/edit extracted text and explicitly proceed to analysis.
- Works on representative Vietnamese, English, and mixed-language samples selected for the contest demo.
- OCR failures and low/empty extraction are clearly surfaced; user can paste text manually.
- Invalid type, corrupt image, and size-limit violations are handled safely.
- The OCR module can be replaced without changing case/report contracts.

## 9. Specification — Investigation Case

### Purpose
Represent one suspicious interaction as a collection of evidence items and their scanner findings.

### Case contents
- Case identifier, created timestamp, lifecycle status, evidence items, findings, recommendations, and derived report data.
- Evidence item types: `message`, `url`, `image`, `ocr_text` (where image and extracted/confirmed text may be represented separately but linked).
- Each finding references one evidence item or is explicitly case-level with its rationale.

### Behavior
- A case can contain two or more evidence items and be analyzed incrementally.
- The system records provenance and scanner status per item.
- Correlation is conservative: a relationship is created only from a concrete shared attribute or user-declared relation; mere co-submission does not prove the items are related.
- If persistence is not implemented, case state may remain in memory/session for the demo; the API and UI still use a stable case identifier during the workflow.

### Acceptance criteria
- Add message and URL to one case and show separate findings under their source items.
- Show an explicit link only when supported (e.g., exact URL extracted from the message); otherwise show no inferred relationship.
- Partial scanner failure does not erase successful evidence results.
- Case identifiers do not expose secrets or personal data.

## 10. Specification — Explainable Risk Assessment

### Purpose
Aggregate structured findings into an understandable risk category without presenting an uncalibrated probability.

### Proposed categories
- `high_risk`: one verified malicious reputation match or multiple strong indicators under documented rules.
- `elevated_risk`: a strong suspicious indicator that warrants pausing and verification.
- `caution`: incomplete evidence or weaker indicators.
- `no_known_signal_found`: checks found no known indicator; explicitly not a safety guarantee.
- `insufficient_information`: analysis failed or evidence is too limited for a meaningful assessment.

Exact rule thresholds and indicator weights are implementation decisions to document and test; avoid hidden LLM scoring.

### Output
- Category and short explanation.
- Contributing finding identifiers and evidence/source references.
- What could not be checked and any contradictory evidence.
- Prioritized safe next action(s).

### Acceptance criteria
- Every risk category is reproducible from a versioned/documented rule set.
- Every reason shown is linked to a finding and evidence/source.
- Model output cannot independently raise risk without a validated structured finding.
- No numeric scam probability is shown.
- Known benign, suspicious, ambiguous, and no-signal cases are tested; absence of a match is not described as proof of safety.

## 11. Specification — AI Security Advisor

### Purpose
Answer user questions about the current case and general safe actions using case findings and curated safety guidance.

### Inputs
- User question, case identifier/context, and retrieved knowledge passages with source metadata where retrieval is available.
- Do not request OTPs, passwords, recovery codes, or full card/bank credentials. If submitted, avoid repeating them and advise the user to take protective action.

### Processing
- Gemini is the proposed model provider behind a backend adapter.
- Provide only relevant case findings and retrieved passages; treat user content and retrieved documents as untrusted data, not instructions.
- Use tool calling only for actual backend capabilities (e.g., retrieve case findings or search curated guidance). The model must not claim it performed a URL/account check unless that tool ran and returned a result.
- Ground sourced claims with title/source references. If retrieval is weak or absent, say so and provide safe general guidance without inventing a citation.
- Do not give definitive accusations about a person or guarantee transaction safety.

### Acceptance criteria
- Answers are relevant to the current case and distinguish case evidence from general guidance.
- When a source is used, the citation maps to a retrieved source; no fabricated source references.
- Weak/no retrieval yields an explicit limitation.
- Questions involving payment, exposed credentials, or a suspected incident receive safe, non-alarmist actions.
- Provider failure is handled with a clear fallback message and does not invent an answer.

## 12. Specification — Investigation Report

### Purpose
Present scanner and Advisor-relevant results as a readable report a user can act on without interpreting raw model output.

### Required sections
1. Overall assessment and plain-language summary.
2. Evidence items submitted and their individual processing status.
3. Findings, each linked to its evidence excerpt/source and verification status.
4. Supported relationships between items, if any.
5. Unknowns, limitations, provider failures, or unavailable checks.
6. Prioritized next actions (including before-payment or incident-response guidance as relevant).

### Acceptance criteria
- User can identify why the case was flagged and what remains unknown.
- Each report statement is traceable to a finding, input, or knowledge source.
- Failed/unavailable checks are visible; they are not omitted in a way that implies success.
- Report uses neutral language, avoids unsupported certainty, and states that “no known signal found” is not a safety guarantee.
- Report remains useful if one scanner fails.

## 13. Shared quality, privacy, and security requirements

- Typed request/response schemas and backend validation for all API boundaries.
- API keys and provider credentials only on the server, in environment/configuration management.
- Upload limits, type validation, safe temporary-file handling, and cleanup.
- No arbitrary server-side URL fetching in this MVP.
- Do not log raw message/image content, secrets, or credentials by default; redact sensitive values where feasible.
- Explicit provider timeout/error states and safe fallback behavior.
- Treat model and retrieved text as untrusted; use structured outputs and validation.
- Make retention and deletion behavior clear before any public deployment.
- Accessible, understandable error and uncertainty language in the UI.

## 14. Cross-feature MVP acceptance

The MVP is acceptable for demo when a user can:

- Submit a message and URL into one investigation.
- Upload a screenshot, inspect/correct OCR text, and analyze it.
- See findings with source, evidence, and verification status.
- See a transparent overall risk category with unknowns and limitations.
- Ask a case-related question and receive appropriately grounded safety advice.
- View a report with concrete next steps.
- Repeat the demo using deterministic test data when external APIs are unavailable, with fixture data visibly labeled.

The demo dataset should include benign, suspicious, and ambiguous scenarios, plus malformed URL, reputation-service failure, poor-quality screenshot, unrelated evidence items, and a sensitive-credential handling case. Dataset size and metrics should be set in the subsequent implementation plan after the contest requirements and available time are confirmed.

## 15. Decisions left to the implementation plan

These are intentionally not settled as part of this product specification:

- Final frontend/backend framework and hosting provider.
- Whether cases persist in PostgreSQL or remain session-scoped for the MVP.
- Which URL reputation provider is available and its quota/cost/terms.
- PaddleOCR version/model configuration and deployment footprint.
- Gemini model/version, schema strategy, quotas, and cost controls.
- Whether to use Qdrant/embedding API or simpler retrieval for the curated knowledge base.
- Detailed scanner rules, risk thresholds, test cases, and ownership by team member.
- Exact retention period and public-deployment privacy notice.
- Exact competition requirements, pending review of the rules PDF.
