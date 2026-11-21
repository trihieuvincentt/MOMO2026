# PaddleOCR proof-of-fit evaluation

**Status:** Pending — not yet measured on the target Render deployment.

## Required sample set

Use synthetic or explicitly consented screenshots only. Keep image files local and do not commit them. Cover Vietnamese, English, mixed language, blurry text, and small text.

## Environment details

- Target service/instance:
- CPU/memory plan:
- Python version:
- PaddleOCR version:
- Model download/cache behavior:
- Model/license review:

## Measurements

| Metric | Local | Render/target |
|---|---:|---:|
| Cold startup (seconds) | pending | pending |
| Warm startup (seconds) | pending | pending |
| Peak RSS (MiB) | pending | pending |
| Model download size (MiB) | pending | pending |
| Request latency p50/p95 (seconds) | pending | pending |

## Quality observations

| Image class | Text accuracy/notes | Failure modes |
|---|---|---|
| Vietnamese | pending | pending |
| English | pending | pending |
| Mixed language | pending | pending |
| Blurry | pending | pending |
| Small text | pending | pending |

## Go/no-go

**Decision:** Pending. Do not designate PaddleOCR as the production primary on Render until measurements and quality observations above are recorded. Gemini Vision remains explicit fallback; user notice is required whenever it receives an image.
