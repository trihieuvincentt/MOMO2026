# Screenshot OCR Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract Vietnamese/English screenshot text with a separate OCR component, allow user review/edit, then submit approved text to the Message Scanner.

**Architecture:** Backend validates image content and limits, stores it temporarily, invokes an OCR adapter (PaddleOCR after deployment proof-of-fit), returns editable text and status, and removes temporary files. Frontend requires explicit user confirmation before analysis.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic, pytest; PaddleOCR/model selected after spike; React/TypeScript, Vitest.

**Spec:** `D:\MOMO2026\scamguard-mvp-spec.md`, Section 8

## Global Constraints

- Allowlist image formats; validate file signature, not just extension/MIME.
- Enforce byte and pixel dimensions; clean temporary uploads.
- OCR text is not analyzed until user review/confirmation.
- No raw image content in logs; manual text fallback is available.
- Validate Vietnamese, English, and mixed-language samples before claiming support.

## Review Focus

- Spoofed `.png` extension with non-image bytes: reject.
- Oversized byte count or pixel dimensions: reject before OCR.
- Corrupt image/PaddleOCR exception: explicit failure and cleanup.
- Blank/low-confidence OCR: do not silently send empty text; offer manual entry.
- OCR text containing prompt-injection-like instructions: treat it as evidence text, not system instruction.

---

### Task 1: Prove OCR engine fit

**Files:** `backend/app/adapters/ocr_engine.py`, `backend/tests/fixtures/ocr/` (consented/synthetic samples), `docs/ocr-proof-of-fit.md`.

**Interfaces:** `OCREngine.extract(image_path: Path, language_hint: str | None) -> OCRResult(text: str, regions: list[OCRRegion], warnings: list[str])`.

- [ ] Select a small representative Vietnamese, English, mixed, low-resolution, and blurry image set; document source/consent.
- [ ] Test installation, CPU/runtime, model download/size, licensing, and extraction quality for the selected PaddleOCR version/model.
- [ ] Record limitations and a pass/fail go/no-go for target deployment. If it fails, stop and propose alternate OCR provider before implementing integration.
- [ ] Commit `docs: record OCR engine proof of fit`.

### Task 2: Validate and process image uploads

**Files:** `backend/app/schemas/ocr.py`, `backend/app/services/ocr_service.py`, `backend/app/api/routes/ocr.py`, `backend/tests/test_ocr_upload.py`, `backend/tests/test_ocr_service.py`.

**Interfaces:** `POST /api/v1/ocr/extract` multipart image + optional language hint; returns `OCRExtraction(id, extracted_text, warnings, status)`.

- [ ] Test content sniffing, allowed formats, byte/pixel limit, corrupt image, engine error, empty extraction, and temporary-file cleanup.
- [ ] Implement bounded temporary storage, content validation, engine injection, cleanup in `finally`, and explicit empty/low-confidence warnings.
- [ ] Run OCR tests; expected pass without persistent image storage.
- [ ] Commit `feat: add bounded screenshot OCR endpoint`.

### Task 3: Add review/edit/confirm UI

**Files:** `frontend/src/features/ocr/OcrReview.tsx`, `frontend/src/features/ocr/OcrReview.test.tsx`, `frontend/src/api/client.ts`.

**Interfaces:** OCR response displays editable text; explicit `Analyze confirmed text` action calls message analysis endpoint with edited text.

- [ ] Test extraction display, edit behavior, OCR failure/manual paste path, and no analysis request before confirmation.
- [ ] Implement review state and confirmation action; preserve clear extraction warnings.
- [ ] Run frontend tests and backend OCR tests; expect pass.
- [ ] Commit `feat: add OCR review and confirm flow`.
