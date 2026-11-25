# URL Access Security Policy

This policy governs future website fetching and browser analysis in ScamGuard. Reputation lookups do not download the submitted page and remain separate from this policy.

## Target validation

Only `http` and `https` URLs are accepted. Before a request or browser navigation, ScamGuard:

- strips fragments and normalizes the hostname with IDNA/punycode;
- rejects credentials embedded in the URL;
- rejects malformed ports and URLs longer than 2048 characters;
- resolves the hostname and rejects localhost, loopback, private, link-local, reserved, unspecified, and multicast addresses;
- repeats validation for every redirect target.

DNS resolution is performed immediately before the controlled request. A production browser worker should run in a restricted container/network namespace as defense in depth.

## Fetch limits

The default `URLSecurityPolicy` is:

| Limit | Default |
|---|---:|
| Connect timeout | 5 seconds |
| Read timeout | 15 seconds |
| Redirects | 3 |
| Response body | 2 MiB |
| URL length | 2048 characters |

`SafeHTTPClient` disables automatic redirect following so each `Location` target can be validated. It accepts only HTML/XHTML content types and does not download arbitrary files.

## Browser limits

`BrowserSecurityPolicy` defines the contract for the Playwright worker:

- downloads disabled;
- form submission disabled;
- maximum navigation timeout: 15 seconds;
- maximum pages per analysis: 6;
- maximum external targets: 5;
- maximum crawl depth: 1.

The browser worker must not enter passwords, OTPs, card numbers, or other credentials, and must not submit login, registration, payment, or verification forms.

## Resource and logging rules

Use `ResourceLimits` before expanding a crawl. Reject work that exceeds page count, external-target count, or depth. Errors should expose a safe reason such as `redirect limit exceeded` or `private target is not allowed`, not response bodies, credentials, API keys, or raw screenshots.

The security modules are implemented in:

- `backend/app/services/url_security.py`
- `backend/app/services/safe_http.py`

They are intentionally independent of the current reputation providers so provider lookups cannot accidentally become arbitrary page fetching. The Browser Snapshot milestone should use these policies before adding Playwright navigation.
