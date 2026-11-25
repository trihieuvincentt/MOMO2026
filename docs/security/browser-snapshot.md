# Browser Snapshot

Milestone 2 adds a controlled browser snapshot service on top of the Milestone 1 URL security policy.

## Service

`backend/app/services/browser_snapshot.py` exposes `BrowserSnapshotService.capture(url)` and returns structured metadata:

- requested and normalized URL;
- final browser URL;
- HTTP status;
- page title;
- redirect chain;
- PNG screenshot bytes.

The service validates the initial target before starting a browser, configures the browser context with downloads disabled, uses a bounded navigation timeout, captures a full-page screenshot, enforces an 8 MiB screenshot limit, and closes the page/context in all paths. The default Playwright factory is optional and is only imported when a real capture is requested.

## Playwright adapter

`backend/app/adapters/playwright_browser.py` owns a headless Chromium process and exposes a narrow adapter interface. It configures a context route handler that validates every network request with the URL security policy. Requests to private, loopback, local, or otherwise invalid targets are aborted. The adapter does not fill or submit forms.

Install the optional dependency and browser binary with:

```bash
uv sync --extra browser
uv run playwright install chromium
```

The Docker image installs the browser extra and Chromium with system dependencies.

## Limits

Default policy values:

- navigation timeout: 15 seconds;
- screenshot limit: 8 MiB;
- downloads: disabled;
- maximum pages: 6;
- maximum external targets: 5;
- maximum crawl depth: 1.

These limits are deliberately conservative. The content extraction milestone should reuse the same context and limits rather than creating unrestricted navigation.

## Safety boundaries

A visual similarity result is an indicator, not a phishing verdict. Browser Snapshot only observes the page. It does not log in, enter credentials, submit forms, download files, or execute user-directed transactions. URL reputation, rendered DOM, link analysis, and evidence fusion remain separate stages.
