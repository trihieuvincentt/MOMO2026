# Scam Dataset Evaluation

This document describes the offline dataset pipeline used to expand and evaluate ScamGuard's rule-based Message Scanner. The datasets are used for feature discovery and regression measurement only. They are not loaded into the production image, sent to Gemini, or used to fine-tune production model weights.

## Sources and licenses

| Dataset | Source | License | Notes |
|---|---|---|---|
| Vietnamese SMS phishing sample | [trannguyenthaituan/vietnamese_sms_phishing_sample](https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_phishing_sample) | CC BY 4.0 | Public CSV sample; source row IDs are retained. |
| Scam dialogues | [adamtc/scam_dialogues](https://huggingface.co/datasets/adamtc/scam_dialogues) | Apache-2.0 | Synthetic dialogue data; reported separately from Vietnamese SMS. |

License names and source row IDs are stored in each cleaned record. Review the upstream dataset pages before redistributing data.

## Reproduce the pipeline

Run from the repository root with `uv`:

```bash
uv run python scripts/fetch_scam_datasets.py
uv run python scripts/evaluate_message_scanner.py \
  --input-dir data/cleaned_datasets \
  --output data/evaluations/message_scanner.json
```

The evaluator also writes a concise Markdown report beside the JSON output. The download script uses fixed public Hugging Face file URLs and writes only to `data/`.

## Cleaning and privacy handling

The cleaner:

- normalizes Unicode to NFC;
- collapses whitespace and uses casefolding for duplicate detection;
- removes duplicate normalized records within each source;
- masks recognizable email addresses, phone numbers, and explicit OTP values;
- retains source, license, source row ID, optional label/category, and synthetic status;
- fails clearly when required text or row-ID columns are missing.

The cleaned text is intended for offline analysis. Do not copy raw or cleaned dataset records into frontend assets, production prompts, logs, or Docker images. The repository's `.dockerignore` excludes `data/`.

## Feature catalog

`backend/app/services/dataset_features.py` extracts explainable families from normalized records:

- credential requests;
- account deactivation threats;
- verification phishing;
- external-link requests;
- prize claims;
- investment promises;
- advance-fee/payment requests;
- urgency;
- secrecy requests;
- brand impersonation.

The generated catalog is `data/scam_feature_catalog.json`. It stores feature-family membership and provenance, not raw production training prompts.

## Evaluation interpretation

The evaluator invokes the existing `analyze_message` function without changing scanner behavior during measurement. It reports:

- total records per source;
- records with at least one scanner finding;
- missed positive labels where a label is available;
- feature-family coverage;
- source row IDs and bounded, redacted excerpts for positive-label misses for offline review;

Observed run on 4,044 cleaned records (the downloaded Vietnamese CSV exposes no label column, so its result is coverage-only):

| Source | Total | Detected | Labeled | Unlabeled | Missed positive labels |
|---|---:|---:|---:|---:|---:|
| Synthetic scam dialogues | 3,837 | 1,095 | 3,837 | 0 | 939 |
| Vietnamese SMS phishing sample | 207 | 131 | 0 | 207 | not measurable |

The evaluator keeps unlabeled coverage separate from labeled missed-positive metrics. These values are baseline coverage measurements, not a certified accuracy score. The synthetic dialogue distribution and labels may not represent live traffic, and not every source has an identical schema or labeling quality.

## Limitations and safety interpretation

- A scanner finding is an indicator, not proof that a message is malicious.
- No finding, no reputation signal, or no campaign match is **not proof of safety**.
- Synthetic labels are evaluation metadata, not ground truth for every real-world message.
- The report does not claim precision, recall, or production accuracy where a reliable labeled negative/positive protocol is unavailable.
- Long multi-turn dialogues can contain scam signals spread across several turns; simple message rules may miss those relationships.
- Dataset-derived rules require focused positive tests and benign counterexamples before being added to production code.
- Dataset contents and generated miss lists may contain sensitive-looking text even after masking; keep them offline and restrict access.
