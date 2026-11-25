# Website Investigation Readiness Runbook

This runbook covers local and staging verification for the ScamGuard website workflow. Do not deploy, push, enable Gemini billing, or trigger live reputation lookups without explicit approval.

## Current workflow

`POST /api/v1/websites/analyze` runs:

1. input URL validation and SSRF checks;
2. website cache lookup (unless force reanalysis is selected);
3. Browser Snapshot using headless Chromium;
4. rendered HTML extraction;
5. bounded link/domain and reputation analysis;
6. Gemini Visual Analysis when `GEMINI_ENABLED=true` and a key is configured;
7. deterministic Evidence Fusion;
8. structured result caching and PostgreSQL graph writes when `DATABASE_URL` is set.

The frontend Website Investigation tab sends the URL, optional claimed brands, and a force-reanalysis flag. It displays snapshot metadata, risk score, evidence reasons, visual indicators, form fields, links, and limitations.

## Safe local smoke test

Start the server with external providers disabled. Use a shell environment scoped to this process; do not print or copy secrets:

```bash
GEMINI_ENABLED=false GEMINI_API_KEY= VIRUSTOTAL_API_KEY= URLHAUS_API_KEY= URLHAUS_AUTH_KEY= DATABASE_URL= uv run uvicorn backend.app.main:app --host 127.0.0.1 --port 8765
```

Verify health and the judge UI:

```bash
curl -i http://127.0.0.1:8765/health
curl -i http://127.0.0.1:8765/
```

Verify the endpoint rejects private targets before navigation:

```bash
curl -i -X POST http://127.0.0.1:8765/api/v1/websites/analyze \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://127.0.0.1/","claimed_brands":[]}'
```

Expected: HTTP 422 and a safe private/local-target message. This check must not start Chromium or call Gemini/reputation providers.

## Browser and Docker validation

The production Docker image must include the `browser` extra and Chromium. On a Docker-enabled host:

```bash
docker build -t scamguard-readiness .
docker run --rm -p 8080:8080 \
  -e GEMINI_ENABLED=false \
  -e VIRUSTOTAL_API_KEY= \
  -e URLHAUS_API_KEY= \
  scamguard-readiness
```

Then check `/health` and `/`. For a real website snapshot, use an approved public test domain in a non-production environment, with Gemini and reputation keys absent. Confirm final URL, status, title and screenshot creation, and check the container logs contain no raw page text, form values, screenshot bytes, API keys, or credentials.

If Chromium or Docker is unavailable, mark this check **not run**; unit tests and a health response are not substitutes for this validation.

## PostgreSQL/cache staging checks

Use a staging database, not production, for these checks:

1. Analyze an approved public test URL once; expect `cache_hit=false`.
2. Repeat with the same URL and same claimed-brand list; expect `cache_hit=true` and no new browser/provider call.
3. Repeat with a different claimed-brand list; expect a cache miss so brand-context-dependent findings are recalculated.
4. Set `force_reanalysis=true`; expect a cache miss and a fresh analysis.
5. Confirm website, source/target links and fused analysis rows are upserted.
6. Run the expired-entry cleanup operation and confirm expired cache rows are removed.

Do not use a real banking, login, payment or personal account URL as a test target.

## Demo configuration and operational limits

- The website route has an in-process sliding-window limit of 20 requests per peer per 60 seconds.
- At most two website analyses run concurrently per process; a saturated process returns HTTP 429 with `Retry-After`.
- These limits are per process, not distributed across multiple Render instances. If scaling beyond one instance, use a shared rate limiter/queue before increasing traffic.
- Use HTTPS for public access.
- Keep Gemini and reputation credentials backend-only; configure them only after approving live-provider spend.
- The cache defaults to a 24-hour TTL. `force_reanalysis` bypasses cached results.
- The workflow does not persist screenshot bytes or raw HTML, and omits full visible-page text from cache. It retains page title, link labels/URLs, form field names, visual indicators and reasons; review retention needs before handling sensitive/private sites.
- PostgreSQL repository cleanup exists, but a recurring scheduler is not configured by this change. Run cleanup through an approved operational schedule before enabling sustained public traffic.
- No finding or cache hit is a guarantee that a website is safe or unchanged.

## Failure handling

| Symptom | Safe response |
|---|---|
| HTTP 422 private/local target | Stop; do not bypass the SSRF guard. |
| HTTP 429 | Wait for `Retry-After`, reduce test concurrency. |
| Browser unavailable | Report the workflow unavailable; install/verify Chromium in the container. Do not silently claim a completed visual scan. |
| Gemini unavailable/disabled | Keep deterministic content/link/reputation results and show visual analysis as unavailable/degraded. |
| Reputation provider unavailable | Preserve partial results and disclose the limitation. |
| Cache hit | Display that the result was reused and provide force-reanalysis when appropriate. |

## Local verification completed

Local API checks run with Gemini, VirusTotal, URLhaus, and PostgreSQL disabled:

- `GET /health` returned HTTP 200 with `{"status":"ok"}`;
- `GET /` returned HTTP 200 and included the Website Investigation tab;
- posting `http://127.0.0.1/` to the website analysis route returned HTTP 422 before browser navigation;
- repeated requests from one peer were bounded and a request beyond the configured 20-per-60-second window returned HTTP 429.

These checks did not exercise Chromium, a real public website, Gemini, reputation providers, or a live PostgreSQL instance. Docker and Playwright/Chromium were unavailable in the verification environment. Fake-connection repository tests cover SQL call structure and cache logic, but are not a staging database smoke test.

## Verification record

Record commit, environment, Docker/Chromium availability, health result, private-target result, cache-hit/miss checks, and any provider status. Never include secret values or raw user page contents in the record.
