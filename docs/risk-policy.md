# ScamGuard Risk Policy

## Policy version

`2026-11-21.v1`

This policy is deterministic. It does not use an LLM score or present a calibrated probability.

## Decision order

1. A `verified_match` finding produces `high_risk` and is referenced by finding ID.
2. An `unverified` finding, unavailable/error scanner, or no successful scan produces `insufficient_information`.
3. A high-severity `suspicious_indicator` produces `elevated_risk`.
4. Two or more distinct suspicious findings produce `elevated_risk`.
5. One weaker suspicious finding produces `caution`.
6. Completed scans with no findings produce `no_known_signal_found`.

## Evidence rules

- Findings are deduplicated by finding ID before aggregation.
- Duplicate IDs are reported in `unknowns` and are not counted twice.
- A verified match and a no-signal result in the same category are both preserved; the assessment remains high risk and exposes the contradiction in `unknowns`.
- Every contributing reason references finding IDs. Case-level unknowns explain unavailable checks and limitations.
- `no_known_signal_found` never means safe.

## Safe actions

Recommendations are curated by risk category and finding category. They advise pausing, independently verifying, avoiding irreversible payment, and securing an affected account. They never request or repeat passwords, OTPs, recovery codes, or full payment credentials.
