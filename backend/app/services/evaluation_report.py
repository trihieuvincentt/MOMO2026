from collections import Counter, defaultdict

from backend.app.schemas.dataset import CleanDatasetRecord
from backend.app.schemas.message import MessageScanRequest
from backend.app.services.dataset_cleaner import mask_sensitive_values, normalize_text
from backend.app.services.dataset_features import extract_feature_families
from backend.app.services.message_scanner import analyze_message


def _deduplicate_records(records: list[CleanDatasetRecord]) -> list[tuple[CleanDatasetRecord, list[CleanDatasetRecord]]]:
    grouped: dict[str, list[CleanDatasetRecord]] = {}
    for record in records:
        key = normalize_text(record.text)
        grouped.setdefault(key, []).append(record)
    return [(duplicates[0], duplicates) for duplicates in grouped.values()]


def evaluate_records(records: list[CleanDatasetRecord]) -> dict:
    sources = defaultdict(
        lambda: {
            "total": 0,
            "detected": 0,
            "missed": 0,
            "labeled": 0,
            "unlabeled": 0,
        }
    )
    feature_coverage: Counter[str] = Counter()
    misses: list[dict] = []
    grouped_records = _deduplicate_records(records)
    for record, provenance in grouped_records:
        result = analyze_message(MessageScanRequest(text=record.text))
        detected = bool(result.findings)
        source_name = "synthetic" if record.is_synthetic else record.source
        bucket = sources[source_name]
        bucket["total"] += 1
        bucket["detected"] += int(detected)
        bucket["labeled"] += int(record.label is not None)
        bucket["unlabeled"] += int(record.label is None)
        bucket["missed"] += int(not detected and record.label == 1)
        feature_coverage.update(extract_feature_families(record).keys())
        if not detected and record.label == 1:
            misses.append(
                {
                    "source": record.source,
                    "source_row_id": record.source_row_id,
                    "source_row_ids": [item.source_row_id for item in provenance],
                    "text_excerpt": mask_sensitive_values(record.text)[:240],
                }
            )
    for bucket in sources.values():
        bucket["interpretation"] = (
            "Labeled positive/negative evaluation"
            if bucket["labeled"]
            else "Unlabeled coverage only; missed positive labels are not measurable"
        )
    return {
        "total": len(grouped_records),
        "input_total": len(records),
        "deduplicated_records": len(records) - len(grouped_records),
        "sources": dict(sources),
        "feature_coverage": dict(feature_coverage),
        "misses": misses,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Offline Message Scanner Evaluation",
        "",
        f"- Input records: {report.get('input_total', report['total'])}",
        f"- Unique records evaluated: {report['total']}",
        f"- Cross-source/within-input duplicates removed: {report.get('deduplicated_records', 0)}",
        "- This report measures baseline rule coverage offline; it is not a production accuracy claim.",
        "- Synthetic labels and no-signal results are not proof of safety.",
        "",
        "## Results by source",
        "",
        "| Source | Total | Detected | Labeled | Unlabeled | Missed positive labels |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for source, metrics in report["sources"].items():
        labeled = metrics.get("labeled", 0)
        unlabeled = metrics.get("unlabeled", max(metrics["total"] - labeled, 0))
        lines.append(
            f"| {source} | {metrics['total']} | {metrics['detected']} | "
            f"{labeled} | {unlabeled} | {metrics['missed']} |"
        )
        lines.append(f"  - {metrics.get('interpretation', 'Offline coverage summary')}")
    lines.extend(["", "## Feature coverage", ""])
    for family, count in sorted(report.get("feature_coverage", {}).items()):
        lines.append(f"- `{family}`: {count} records")
    lines.extend(["", f"Positive-label misses retained for review: {len(report['misses'])}", ""])
    return "\n".join(lines)
