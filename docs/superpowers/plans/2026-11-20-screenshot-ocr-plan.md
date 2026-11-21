# Screenshot OCR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract Vietnamese/English screenshot text with a separate OCR component, allow user review/edit, then submit approved text to the Message Scanner.

**Architecture:** Backend validates image content and limits, stores it temporarily, invokes an OCR adapter with PaddleOCR as the primary engine after target-deployment proof-of-fit, and uses Gemini Vision as an explicit fallback when PaddleOCR is unavailable or fails. The response always exposes `ocr_source` (`paddleocr` or `gemini_vision`) and uncertainty notes. Frontend requires explicit user review/edit/confirmation before Message Scanner analysis; temporary images and sensitive OCR text are cleaned according to retention policy.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, pytest; PaddleOCR/model selected after spike; React/TypeScript, Vitest.

**Spec:** `../specs/2026-11-20-scamguard-mvp-design.md`, Section 8

## Global Constraints

- Allowlist image formats; validate file signature, not just extension/MIME.
- Enforce byte and pixel dimensions; clean temporary uploads.
- Run PaddleOCR proof-of-fit on the target public deployment environment (Render or selected alternative), not only on developer local machines.
- Measure startup time, memory usage, model download behavior, and OCR request latency.
- Test Vietnamese, English, mixed-language, blurry, and small-text images.
- Use Gemini Vision only as an explicit fallback for extraction; show `ocr_source` and notify users when the image is sent to Gemini.
- OCR text is not analyzed until user review/confirmation; manual text fallback is available.
- No raw image or sensitive OCR text in logs; clean temporary data after the active case needs it.

## Review Focus

- Spoofed `.png` extension with non-image bytes: reject.
- Oversized byte count or pixel dimensions: reject before OCR.
- Corrupt image/PaddleOCR exception: explicit failure and cleanup.
- Blank/low-confidence OCR: do not silently send empty text; offer manual entry.
- OCR text containing prompt-injection-like instructions: treat it as evidence text, not system instruction.

---

### Task 1: Prove PaddleOCR fit on the public deployment target

**Files:** `backend/app/adapters/ocr_engine.py`, `backend/tests/fixtures/ocr/` (consented/synthetic samples), `scripts/measure_ocr_runtime.py`, `docs/superpowers/evaluations/2026-11-21-ocr-proof-of-fit.md`.

**Interfaces:** `OCREngine.extract(image_path: Path, language_hint: str | None) -> OCRResult(text: str, regions: list[OCRRegion], warnings: list[str])`; the evaluation report records `ocr_source`, startup seconds, peak memory, model download behavior, request latency, and per-image quality notes.

- [ ] Select representative Vietnamese, English, mixed-language, blurry, and small-text images; document source/consent and do not commit sensitive images.
- [ ] Test PaddleOCR installation, model download/size, license, CPU/runtime, startup time, peak RAM, request latency, and extraction quality locally and on Render/target deployment.
- [ ] Record a pass/fail go/no-go for primary use in the target deployment. If PaddleOCR fails or exceeds the deployment budget, keep the adapter contract and enable Gemini Vision fallback rather than blocking the product.
- [ ] Commit `docs: record PaddleOCR deployment proof of fit`.

### Task 2: Add explicit Gemini Vision fallback contract

**Files:** `backend/app/adapters/gemini_vision.py`, `backend/app/schemas/ocr.py`, `backend/tests/test_gemini_vision_fallback.py`.

**Interfaces:** `GeminiVisionExtractor.extract(image_bytes: bytes, language_hint: str | None) -> OCRResult`; `OCRResult` includes `text`, `warnings`, `ocr_source`, `provider_notice`, and optional regions/confidence.

- [x] Test valid extraction, unreadable/uncertain text, provider timeout, malformed response, and that `ocr_source == "gemini_vision"` plus a provider notice is returned.
- [x] Implement extraction-only prompt: do not ask Gemini Vision to make a scam verdict; mark unreadable portions and return uncertainty notes.
- [x] Ensure fallback is invoked only after PaddleOCR failure/unavailability or an explicit configured fallback mode.
- [x] Run focused tests; expect pass with mocked Gemini client.
- [x] Commit `feat: add explicit Gemini Vision OCR fallback`.

### Task 3: Validate and process image uploads

**Files:** `backend/app/schemas/ocr.py`, `backend/app/services/ocr_service.py`, `backend/app/api/routes/ocr.py`, `backend/tests/test_ocr_upload.py`, `backend/tests/test_ocr_service.py`.

**Interfaces:** `POST /api/v1/ocr/extract` multipart image + optional language hint; returns `OCRExtraction(id, extracted_text, warnings, status, ocr_source, provider_notice, retention_expires_at)`.

- [x] Test content sniffing, allowed formats, byte/pixel limit, corrupt image, PaddleOCR failure followed by Gemini Vision fallback, explicit provider notice, empty extraction, and temporary-file cleanup.
- [x] Implement bounded temporary storage, content validation, primary/fallback engine injection, cleanup in `finally`, explicit `ocr_source`, user-facing notice when Gemini receives the image, and empty/low-confidence warnings.
- [x] Ensure sensitive text is not written to logs and temporary image/text retention ends after the active case requirement.
- [x] Run OCR tests; expected pass without persistent image storage.
- [x] Commit `feat: add bounded screenshot OCR endpoint`.

### Task 4: Add review/edit/confirm UI

**Files:** `frontend/src/features/ocr/OcrReview.tsx`, `frontend/src/features/ocr/OcrReview.test.tsx`, `frontend/src/api/client.ts`.

**Interfaces:** OCR response displays editable text; explicit `Analyze confirmed text` action calls message analysis endpoint with edited text.

- [ ] Test extraction display, edit behavior, OCR failure/manual paste path, and no analysis request before confirmation.
- [ ] Implement review state and confirmation action; preserve clear extraction warnings.
- [ ] Run frontend tests and backend OCR tests; expect pass.
- [ ] Commit `feat: add OCR review and confirm flow`.
