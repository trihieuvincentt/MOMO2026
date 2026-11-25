# PostgreSQL Website Cache

Milestone 7 adds PostgreSQL-backed reuse for website analysis and a graph store for link relationships.

## Cache

`WebsiteCacheRepository` stores a normalized URL, structured JSONB payload, expiry timestamp, and update timestamp in `scamguard_websites`.

- URL keys are normalized with lowercase scheme/IDNA hostname, default `/` path, query preserved, and fragment removed.
- `get()` returns only unexpired entries.
- `save()` uses a parameterized upsert.
- `cleanup_expired()` removes entries whose TTL has elapsed.
- `WebsiteAnalysisCache` provides a default TTL and a `force_reanalysis` bypass.

The cache payload is structured analysis data, not an API key, credential, raw form value, or hidden model reasoning.

## Website graph

`WebsiteGraphRepository` stores:

- website metadata in `scamguard_websites`;
- source-to-target relationships in `scamguard_website_links`;
- fused analysis results in `scamguard_website_analyses`.

Links use a composite source/target key so repeated extraction updates the relationship rather than creating duplicates. All writes use parameterized SQL and JSONB payloads.

## Reuse policy

The eventual website orchestration flow should:

1. normalize the URL;
2. check the cache;
3. reuse a non-expired structured result unless `force_reanalysis` is requested;
4. run Browser Snapshot, extraction, link analysis, visual analysis, and fusion only on a miss;
5. write website, links, and analysis results;
6. run periodic expiry cleanup.

Screenshots and raw HTML should receive shorter retention than compact structured results. Cleanup policy should be added before public demo traffic is enabled.
