# Judge Frontend Design

## Intent
Provide a judge-accessible ScamGuard web UI that exercises the deployed backend without exposing API keys. The UI must support message scanning, URL reputation checks, and screenshot OCR with an explicit human review/confirmation gate before OCR text is sent to Message Scanner.

## Goals
- Serve a static frontend from the existing FastAPI service and same origin.
- Provide Message Scanner, URL Scanner, and Screenshot OCR workflows.
- Show status, findings, limitations, risk/severity, OCR source, and Gemini provider notice.
- Keep OCR text local in the browser until the user clicks `Confirm & scan`.
- Show actionable errors without exposing secrets.

## Non-goals
- No authentication, case-management UI, AI Security Advisor, or report editor in this slice.
- No API keys in browser code.
- No automatic OCR-to-message scan.

## Approach
Use plain HTML, CSS, and JavaScript served by FastAPI from `frontend/`. Same-origin relative API paths avoid CORS and keep the browser credential-free. A small frontend module owns API calls and UI state; OCR confirmation is the only path that calls Message Scanner with extracted text.

## User flow
```text
Choose tab → submit input → render API result
OCR: upload image → display editable extracted text + source notice
     → user edits/reviews → Confirm & scan → call message scanner
```

## Constraints
- OCR upload uses `multipart/form-data` to `/api/v1/ocr/extract`.
- Message scanner uses `{ "text": string }`.
- URL scanner uses `{ "url": string }`.
- API errors are rendered as generic user-facing messages; raw secrets are never displayed.
- Existing backend tests and behavior remain unchanged.
