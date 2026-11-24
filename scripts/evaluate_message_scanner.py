import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.schemas.dataset import CleanDatasetRecord
from backend.app.services.evaluation_report import evaluate_records, render_markdown


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default="data/cleaned_datasets")
    parser.add_argument("--output", default="data/evaluations/message_scanner.json")
    args = parser.parse_args()
    records = [
        CleanDatasetRecord.model_validate_json(line)
        for path in sorted(Path(args.input_dir).glob("*.jsonl"))
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    report = evaluate_records(records)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    output.with_suffix(".md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"total": report["total"], "sources": report["sources"], "misses": len(report["misses"])}))


if __name__ == "__main__":
    main()
