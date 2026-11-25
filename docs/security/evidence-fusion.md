# Evidence Fusion

Milestone 6 combines visual, rendered-content, link/domain, and reputation signals into one explainable assessment.

## Fusion behavior

`EvidenceFusionService.fuse(...)` accepts independent results from:

- Visual Gemini analysis;
- Website Content Extraction;
- Link/Domain Analysis;
- reputation providers.

It returns:

- bounded score from 0 to 100;
- category: `high_risk`, `elevated_risk`, `caution`, `no_known_signal_found`, or `insufficient_information`;
- reasons with description, evidence source, severity, and points;
- explicit unknowns for unavailable/degraded inputs;
- limitations for interpretation boundaries.

A visual signal by itself cannot produce `high_risk`. High risk requires corroboration such as a reputation match, brand/domain mismatch, sensitive form evidence, or multiple independent signals. An external link alone is not maliciousness proof, and no reputation match is not a safety guarantee.

## Risk adapter

`fusion_to_risk_assessment` converts the fusion result into the existing `RiskAssessment` schema while preserving:

- category;
- evidence-source contribution IDs;
- explanation;
- unknowns;
- safe next-step recommendations;
- a separate evidence-fusion policy version.

This allows existing reports and recommendation UI to consume the result without letting Gemini bypass the deterministic risk policy.

## API

`POST /api/v1/evidence/fuse` accepts structured visual/content/link results plus a bounded reputation-match count. It is intended as a composition endpoint for the upcoming website investigation orchestration flow.

The response exposes reasons and limitations directly so the frontend can show why a website received its category. It does not expose API keys, raw screenshots, form values, or hidden model reasoning.
