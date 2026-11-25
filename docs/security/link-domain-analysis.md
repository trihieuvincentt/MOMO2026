# Link and Domain Analysis

Milestone 4 adds bounded analysis of links extracted from rendered website content.

## Capabilities

`analyze_links`:

- normalizes URLs and removes fragments;
- deduplicates repeated links;
- classifies links as internal or external by registrable site domain;
- preserves visible text and coarse role;
- identifies login, registration, verification, and payment targets for deeper review;
- detects claimed-brand/domain mismatch for sensitive external actions;
- optionally checks a bounded set of external targets with the existing reputation provider;
- returns reputation details without treating an absent signal as safe;
- reports limits and provider failures explicitly.

An external link alone is not a maliciousness verdict. It is an observation that can become more important when combined with a sensitive role, brand mismatch, reputation match, or other evidence.

## Limits

The default deep-analysis selection is bounded to five external targets. The service accepts a lower `max_external_targets` for callers with stricter budgets. It never sends internal links to reputation providers and never crawls a link by itself.

## API

`POST /api/v1/links/analyze` accepts a source URL, extracted link metadata, and optional claimed brands. The source URL is validated through the Milestone 1 SSRF policy before analysis.

The response includes:

- analyzed links;
- relationship (`internal`/`external`);
- role;
- indicators;
- severity;
- whether deep analysis is recommended;
- bounded deep-analysis targets;
- limitations.

The next milestone can use `deep_analysis_targets` to invoke Browser Snapshot at depth one, subject to the same URL security and resource policies.
