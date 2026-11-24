import argparse
import csv
import json
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.services.dataset_cleaner import clean_records

SOURCES = {
    "vietnamese_sms": {
        "url": "https://huggingface.co/datasets/trannguyenthaituan/vietnamese_sms_phishing_sample/resolve/main/sample_300.csv",
        "source": "trannguyenthaituan/vietnamese_sms_phishing_sample",
        "license": "CC BY 4.0",
        "format": "csv",
    },
    "scam_dialogues": {
        "url": "https://huggingface.co/datasets/adamtc/scam_dialogues/resolve/main/scam-dialogues-train-text.json",
        "source": "adamtc/scam_dialogues",
        "license": "Apache-2.0",
        "format": "json",
    },
}


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "ScamGuard-dataset-prep/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310
        return response.read()


def load_rows(config: dict, payload: bytes) -> list[dict]:
    if config["format"] == "csv":
        return list(csv.DictReader(payload.decode("utf-8-sig").splitlines()))
    else:
        decoded = json.loads(payload)
        if isinstance(decoded, dict) and "data" in decoded:
            decoded = decoded["data"]
        if not isinstance(decoded, list):
            raise ValueError("Dataset JSON must contain a list of rows")
        return [dict(row, __row_id=str(index)) for index, row in enumerate(decoded)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="data/cleaned_datasets")
    parser.add_argument("--source", choices=[*SOURCES, "all"], default="all")
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    names = SOURCES if args.source == "all" else {args.source: SOURCES[args.source]}
    for name, config in names.items():
        rows = load_rows(config, fetch(config["url"]))
        if name == "vietnamese_sms":
            records = clean_records(rows, source=config["source"], license_name=config["license"], text_field="text", id_field="message_id", label_field="label")
        else:
            records = clean_records(rows, source=config["source"], license_name=config["license"], text_field="dialogue", id_field="__row_id", label_field="label", category_field="type", is_synthetic=True)
        target = output_dir / f"{name}.jsonl"
        with target.open("w", encoding="utf-8") as handle:
            for index, record in enumerate(records):
                data = record.model_dump(mode="json")
                handle.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"{name}: {len(records)} cleaned records -> {target}")


if __name__ == "__main__":
    main()
