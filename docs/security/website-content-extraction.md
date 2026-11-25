# Website Content Extraction

Milestone 3 extracts structured content from the rendered DOM returned by Browser Snapshot. It does not fetch arbitrary URLs or crawl links; URL access remains governed by the Milestone 1 security policy.

## Extracted fields

`extract_website_content(html, base_url=...)` returns:

- page title;
- meta description;
- H1/H2/H3 headings;
- normalized visible text;
- forms and action URLs;
- form method and input metadata;
- sensitive-field indicators without retaining input values;
- image URLs and alt text;
- links with visible text, normalized URL, target domain, `rel`, `target`, internal/external classification, and a coarse role.

Supported link roles currently include login, registration, verification, payment, and promotion/bonus signals. An external link is an observation, not an automatic maliciousness verdict.

## Safety boundaries

The extractor ignores `script`, `style`, `noscript`, and `template` text. It ignores `javascript:`, `mailto:`, `tel:`, and fragment-only links. Form values are never extracted, including password, OTP, card, and account fields. Forms are metadata only; no form is submitted.

The parser uses Python's standard-library `HTMLParser`, so it can be used offline in tests and does not introduce a new HTML-fetching dependency. `WebsiteContentService` composes the parser with a `BrowserSnapshot` and uses the snapshot's final URL as the base for relative links.

## Next milestone

Milestone 4 can consume `WebsiteContent.links` for internal/external relationship analysis, domain mismatch detection, and bounded selection of external targets for deeper analysis. It should reuse the existing URL validation and `ResourceLimits` rather than navigating every extracted link.
