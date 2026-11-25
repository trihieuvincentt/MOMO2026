# PostgreSQL Website Cache

Milestone 7 adds PostgreSQL-backed reuse for website analysis and a graph store for link relationships.

## Cache

`WebsiteCacheRepository` stores a normalized URL, structured JSONB payload, expiry timestamp, and update timestamp in `scamguard_websites`.

- URL keys are normalized with lowercase scheme/IDNA hostname, default `/` path, query preserved, and fragment removed.
- `get()` returns only unexpired entries.
- `save()` uses a parameterized upsert.
- `cleanup_expired()` removes entries whose TTL has elapsed.
- `WebsiteAnalysisCache` provides a default TTL and a `force_reanalysis` bypass.

The website investigation workflow now performs cache lookup before browser capture, bypasses the cache when `force_reanalysis` is requested, and saves the website, links, and fused analysis graph. Cache context includes claimed brands so a result based on different brand claims is not reused. The cache stores extracted metadata and risk reasons, but omits full rendered visible text, raw HTML, and screenshot bytes.

Screenshots and raw HTML are not persisted by this workflow. The cache payload is structured analysis data, not an API key, credential, raw form value, raw page body, or hidden model reasoning.

## Website graph

`WebsiteGraphRepository` stores:

- website metadata in `scamguard_websites`;
- source-to-target relationships in `scamguard_website_links`;
- fused analysis results in `scamguard_website_analyses`.

Links use a composite source/target key so repeated extraction updates the relationship rather than creating duplicates. All writes use parameterized SQL and JSONB payloads.

## Reuse policy

The website investigation flow at `POST /api/v1/websites/analyze`:

1. normalizes the URL and checks cache before browser startup;
2. reuses an unexpired result when its claimed-brand context matches;
3. bypasses cache on `force_reanalysis: true`;
4. on a miss, runs Browser Snapshot, extraction, link analysis, optional Visual Gemini analysis, and evidence fusion;
5. stores the structured result and, when PostgreSQL is configured, upserts website, links, and fused analysis graph;
6. returns `cache_hit` so the UI can distinguish reused results.

The in-memory fallback has a 24-hour TTL and key normalization. A scheduled cleanup job is still an operational follow-up; the repository exposes `cleanup_expired()` for it. The current workflow does not persist screenshot bytes or raw HTML. Cache payload omits the full visible-text field, although it retains extracted titles, link labels/URLs, form field names, visual indicators, and risk reasons.
