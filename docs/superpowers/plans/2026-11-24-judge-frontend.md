# Judge Frontend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a same-origin judge demo UI for Message Scanner, URL Scanner, and OCR review/confirm workflows.

**Architecture:** FastAPI serves `frontend/index.html`, `frontend/app.js`, and `frontend/styles.css` as static assets. Browser JavaScript uses relative `/api/v1/...` endpoints; OCR extraction updates an editable draft only, and the Message Scanner request is made exclusively from the explicit confirmation handler.

**Tech Stack:** FastAPI `StaticFiles`/`FileResponse`, vanilla HTML/CSS/JavaScript, pytest.

**Spec:** `docs/superpowers/specs/2026-11-24-judge-frontend-design.md`

## Global Constraints

- Never put API keys or database credentials in frontend files.
- OCR text must not be sent to Message Scanner before explicit user confirmation.
- Use `/api/v1/message/analyze` with `{ "text": string }`.
- Use `/api/v1/url/analyze` with `{ "url": string }`.
- Use `/api/v1/ocr/extract` with multipart image upload.
- Preserve backend behavior and run the complete existing pytest suite.

## Review Focus

- OCR succeeds but user edits the extracted text: only edited text is scanned after confirmation.
- OCR succeeds with `gemini_vision`: provider notice and source are visible.
- OCR request fails or returns malformed JSON: UI shows a safe error and does not scan.
- Message/URL API returns non-2xx: UI shows an error without dumping response secrets.
- Direct page load and refresh: static assets resolve from the same-origin FastAPI service.

---

### Task 1: Static frontend serving

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/app.js`
- Create: `frontend/styles.css`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_frontend_route.py`

**Interfaces:**
- Consumes: existing FastAPI `app`.
- Produces: `GET /` returns the judge UI; static `/app.js` and `/styles.css` resolve.

- [ ] **Step 1: Write the failing route test**

Add tests asserting `GET /` returns 200 and contains `ScamGuard`, and `/app.js` plus `/styles.css` return 200.

- [ ] **Step 2: Run the route test to verify it fails**

Run: `uv run pytest backend/tests/test_frontend_route.py -q`
Expected: FAIL because no frontend route/assets exist.

- [ ] **Step 3: Implement static serving**

Mount `frontend` at `/static` and return `frontend/index.html` from `GET /`. Keep API routes unchanged. Add responsive semantic markup with tabs/cards for the three workflows.

- [ ] **Step 4: Run the route test**

Run: `uv run pytest backend/tests/test_frontend_route.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add frontend backend/app/main.py backend/tests/test_frontend_route.py
git commit -m "feat: add judge frontend shell"
```

### Task 2: Message and URL scanner UI

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`
- Test: `backend/tests/test_frontend_contract.py`

**Interfaces:**
- Consumes: same-origin `/api/v1/message/analyze` and `/api/v1/url/analyze`.
- Produces: forms that POST exact payloads and render structured JSON safely in the result panel.

- [ ] **Step 1: Write failing contract tests**

Assert frontend source contains the two endpoint paths, payload keys `text` and `url`, and result containers for findings/limitations.

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest backend/tests/test_frontend_contract.py -q`
Expected: FAIL because the source has not implemented scanner handlers.

- [ ] **Step 3: Implement handlers**

Implement `scanMessage(text)` and `scanUrl(url)` using `fetch`, JSON headers, non-2xx handling, and DOM rendering through `textContent`/created nodes rather than injecting API response HTML.

- [ ] **Step 4: Run contract tests and full backend suite**

Run: `uv run pytest backend/tests/test_frontend_contract.py -q && uv run pytest -q`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend backend/tests/test_frontend_contract.py
git commit -m "feat: add message and URL scanner workflows"
```

### Task 3: OCR review, edit, and explicit confirmation

**Files:**
- Modify: `frontend/index.html`
- Modify: `frontend/app.js`
- Modify: `frontend/styles.css`
- Modify: `backend/tests/test_frontend_contract.py`

**Interfaces:**
- Consumes: `/api/v1/ocr/extract` response fields `extracted_text`, `ocr_source`, `provider_notice`, `warnings`, and `/api/v1/message/analyze`.
- Produces: `extractOcr(file)` and `confirmOcrAndScan()` flow; confirmation button is disabled until OCR text exists and never auto-submits message scan.

- [ ] **Step 1: Write failing OCR contract tests**

Assert source contains multipart OCR upload, `ocr_source`, `provider_notice`, an editable textarea, a confirm control, and that the OCR success handler does not call `scanMessage` until the confirm handler.

- [ ] **Step 2: Run tests to verify failure**

Run: `uv run pytest backend/tests/test_frontend_contract.py -q`
Expected: FAIL for missing OCR workflow/confirmation contract.

- [ ] **Step 3: Implement OCR flow**

Upload via `FormData`; render extracted text into an editable textarea, source badge, provider notice, and warnings. Keep the button disabled during extraction and until non-empty text is present. `confirmOcrAndScan()` reads the current textarea value and calls the existing message scanner function only on click.

- [ ] **Step 4: Run all tests**

Run: `uv run pytest -q`
Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add frontend backend/tests/test_frontend_contract.py
git commit -m "feat: add OCR review and confirmation workflow"
```

### Task 4: Production smoke verification

**Files:**
- Modify: `Dockerfile` only if static assets are not included by the existing `COPY`.
- Modify: `docs/superpowers/evaluations/2026-11-21-ocr-proof-of-fit.md` only with observed target results.

- [ ] **Step 1: Run complete tests**

Run: `uv run pytest -q`
Expected: all tests pass.

- [ ] **Step 2: Build/run verification**

Start the app using the project run path and verify `GET /`, `/health`, and the three relative API calls against a configured environment. Do not record secrets or real sensitive evidence.

- [ ] **Step 3: Commit any documentation-only measurement update**

Only record actual measurements; do not claim PaddleOCR on Render when `OCR_ENGINE=gemini_vision` is configured.
