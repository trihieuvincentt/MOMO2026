# Campaign Intelligence Design

## Intent
Make ScamGuard different from a one-shot general AI answer by extracting reusable scam artifacts from evidence, matching them against previously stored cases, and reporting only evidence-backed campaign signals.

## MVP goals
- Detect normalized artifacts from message/OCR text: brands, URLs, phone numbers, monetary amounts, distinctive scam phrases, and scam patterns.
- Store artifacts inside the existing case JSON payload so Neon persistence remains backward-compatible.
- Compare a newly analyzed case with prior cases without exposing raw unrelated case content.
- Report shared artifacts and match strength; never invent prior-case counts or campaign names.
- Preserve current scanner, risk, Gemini, and report behavior.

## Non-goals
- No graph database, user identity, public case browsing, or global campaign dashboard.
- No claim that an absence of matches means safety.
- No raw cross-user evidence disclosure; only normalized shared artifact values and counts.
- No model-generated campaign match without deterministic artifact support.

## Architecture
Artifact extraction is deterministic and runs after evidence scanners. A repository query returns prior cases, the matcher computes intersections over normalized artifacts, and the report exposes `artifacts` plus `campaign_matches`. Existing Postgres payload JSON remains the storage boundary.

## Safety constraints
- Do not store API keys or image bytes in artifacts.
- Preserve source evidence IDs for traceability.
- Redact or avoid raw sensitive content; payment account and credential values are not extracted in this MVP.
- A campaign match requires at least two shared normalized artifacts or one high-confidence exact URL/phone artifact.
- Match counts are based only on persisted cases returned by the repository.
