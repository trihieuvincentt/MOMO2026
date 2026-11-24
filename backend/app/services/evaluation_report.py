from collections import Counter, defaultdict

from backend.app.schemas.dataset import CleanDatasetRecord
from backend.app.schemas.message import MessageScanRequest
from backend.app.services.dataset_features import extract_feature_families
from backend.app.services.message_scanner import analyze_message


def evaluate_records(records: list[CleanDatasetRecord]) -> dict:
    sources = defaultdict(lambda: {"total": 0, "detected": 0, "missed": 0})
    feature_coverage: Counter[str] = Counter()
    misses: list[dict] = []
    for record in records:
        result = analyze_message(MessageScanRequest(text=record.text))
        detected = bool(result.findings)
        bucket = sources["synthetic" if record.is_synthetic else record.source]
        bucket["total"] += 1
        bucket["detected"] += int(detected)
        bucket["missed"] += int(not detected and record.label == 1)
        feature_coverage.update(extract_feature_families(record).keys())
        if not detected and record.label == 1:
            misses.append(
                {
                    "source": record.source,
                    "source_row_id": record.source_row_id,
                    "text": record.text,
                }
            )
    return {
        "total": len(records),
        "sources": dict(sources),
        "feature_coverage": dict(feature_coverage),
        "misses": misses,
    }


def render_markdown(report: dict) -> str:
    lines = [
        "# Offline Message Scanner Evaluation",
        "",
        f"- Total records: {report['total']}",
        "- This report measures baseline rule coverage offline; it is not a production accuracy claim.",
        "- Synthetic labels and no-signal results are not proof of safety.",
        "",
        "## Results by source",
        "",
        "| Source | Total | Detected | Missed positive labels |",
        "|---|---:|---:|---:|",
    ]
    for source, metrics in report["sources"].items():
        lines.append(
            f"| {source} | {metrics['total']} | {metrics['detected']} | {metrics['missed']} |"
        )
    lines.extend(["", "## Feature coverage", ""])
    for family, count in sorted(report.get("feature_coverage", {}).items()):
        lines.append(f"- `{family}`: {count} records")
    lines.extend(["", f"Positive-label misses retained for review: {len(report['misses'])}", ""])
    return "\n".join(lines)
