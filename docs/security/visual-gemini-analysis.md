# Visual Gemini Analysis

Milestone 5 adds structured visual analysis on top of Browser Snapshot. Gemini receives the rendered PNG screenshot and returns visual evidence; it does not receive credentials or form values, and visual similarity alone is never treated as a phishing verdict.

## Structured result

The analyzer returns:

- `site_type` such as banking, wallet, ecommerce, social, casino, or unknown;
- visible detected brands;
- visible form purposes and field names;
- sensitive data categories requested;
- visual indicators with category, description, evidence, and confidence from 0 to 1;
- provider limitations and status.

Allowed visual indicator examples include `brand_impersonation`, `sensitive_form`, `visual_mismatch`, `credential_collection`, `suspicious_claim`, and `unusual_redirect`.

## Safety behavior

- only PNG/JPEG screenshot bytes are accepted;
- the Gemini prompt instructs the model not to declare definitive phishing from appearance alone;
- deterministic context (title, final URL, claimed brands, and existing evidence) is bounded before being sent;
- malformed provider JSON is rejected rather than treated as a successful analysis;
- provider failures return degraded/unavailable structured results while deterministic evidence remains usable;
- limitations explicitly require combining visual evidence with HTML, links, domain, and reputation signals.

## API

`POST /api/v1/visual/analyze` accepts:

```json
{
  "url": "https://example.com",
  "claimed_brands": ["Example Bank"],
  "deterministic_context": "login form requests password and OTP"
}
```

The endpoint captures a secure Browser Snapshot first, then invokes Gemini Vision when configured. It returns visual findings plus normalized/final URL and page title. API keys remain backend-only.

## Files

- `backend/app/adapters/gemini_visual.py` — Gemini Vision transport and validation.
- `backend/app/services/visual_analysis.py` — snapshot/context composition and degraded mode.
- `backend/app/api/routes/visual.py` — HTTP endpoint.

The next milestone should fuse this result with Link/Domain Analysis, content forms, and reputation signals before assigning an overall risk level.
