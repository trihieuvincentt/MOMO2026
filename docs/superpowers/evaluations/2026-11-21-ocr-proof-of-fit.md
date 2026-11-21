# PaddleOCR proof-of-fit evaluation

**Status:** Local CPU measurement complete on Windows; Render/target deployment measurement pending.

## Local environment

- OS: Windows 11 x64
- Python: 3.12.9
- PaddleOCR: 3.7.0
- PaddlePaddle CPU: 3.3.1
- OCR model: PaddleOCR 3 pipeline (`PP-OCRv6_medium_det` / `PP-OCRv6_medium_rec`)
- Sample: synthetic English PNG (900 × 240); no personal/sensitive data
- Model weights: downloaded automatically on first initialization and cached under the user PaddleX model cache.

## Local measurements

| Metric | Local CPU result |
|---|---:|
| Cold startup including model initialization/download | Not isolated from download; initial model download occurred |
| Warm startup (cached weights) | 18.21 seconds |
| RSS after model startup | 501.75 MiB |
| Synthetic image request latency | 12.28 seconds |
| Extracted characters | 28 |
| Warnings | 0 |

These values are one Windows CPU sample, not a representative benchmark or a service-level objective. Measure multiple images and p50/p95 on target hardware before production sizing.

## Failure observed and mitigation

The first local inference failed in PaddlePaddle 3.3.1's oneDNN executor with `ConvertPirAttribute2RuntimeAttribute not support [pir::ArrayAttribute<pir::DoubleAttribute>]`. Setting PaddleOCR `enable_mkldnn=False` in the CPU adapter allowed the synthetic local inference to complete. Keep this option unless target-platform testing proves a better configuration.

## Sample coverage

| Image class | Local evidence | Render evidence |
|---|---|---|
| English synthetic | One sample completed; 28 output characters | pending |
| Vietnamese | pending | pending |
| Mixed language | pending | pending |
| Blurry | pending | pending |
| Small text | pending | pending |

## Render setup and measurement

Render configuration is in `render.yaml` and installs `--extra ocr`. Deploy it to a private/staging Render Web Service, then execute:

```bash
uv run python scripts/measure_ocr_runtime.py <consented-synthetic-image-path> --language en
```

Repeat with Vietnamese/mixed/blurry/small-text samples and record startup, RSS, request latency, model download/cache behavior, and quality here. Do not mark production go until target measurements are recorded.

## Go/no-go

- Local adapter/runtime: **GO for continued integration testing with CPU oneDNN disabled**.
- Render production primary: **PENDING** until target deployment memory/latency and language-quality tests are complete.
- Gemini Vision remains explicit fallback; users must be told whenever their image is sent to Gemini.
