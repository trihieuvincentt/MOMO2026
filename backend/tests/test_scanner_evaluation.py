from backend.app.services.evaluation_report import evaluate_records
from backend.app.schemas.dataset import CleanDatasetRecord


def record(text, label=1, source="sms", synthetic=False):
    return CleanDatasetRecord(source=source, license_name="test", source_row_id=text[:5], text=text, normalized_text=text.casefold(), label=label, is_synthetic=synthetic)


def test_evaluation_separates_sources_and_reports_misses():
    report = evaluate_records([
        record("Send your OTP immediately", label=1),
        record("The library is open today", label=0),
        record("Guaranteed profit deposit now", label=1, source="synthetic", synthetic=True),
    ])
    assert report["total"] == 3
    assert report["sources"]["sms"]["total"] == 2
    assert report["sources"]["synthetic"]["total"] == 1
    assert "detected" in report["sources"]["sms"]
    assert isinstance(report["misses"], list)
    assert "feature_coverage" in report
    assert isinstance(report["feature_coverage"], dict)
    assert report["sources"]["sms"]["labeled"] == 2
    assert report["sources"]["sms"]["unlabeled"] == 0


def test_evaluation_deduplicates_across_sources_and_redacts_miss_text():
    duplicate_a = record("Your account is suspended; provide SSN 123-45-6789", label=1, source="sms")
    duplicate_b = record("your ACCOUNT is suspended; provide SSN 123-45-6789", label=1, source="synthetic", synthetic=True)
    report = evaluate_records([duplicate_a, duplicate_b])

    assert report["total"] == 1
    assert report["deduplicated_records"] == 1
    assert report["sources"]["sms"]["total"] == 1
    assert "123-45-6789" not in report["misses"][0]["text_excerpt"]
    assert report["misses"][0]["text_excerpt"] != duplicate_a.text
    assert len(report["misses"][0]["source_row_ids"]) == 2


def test_evaluation_reports_unlabeled_coverage_without_positive_miss_claims():
    report = evaluate_records([record("A normal message", label=None)])

    assert report["sources"]["sms"]["labeled"] == 0
    assert report["sources"]["sms"]["unlabeled"] == 1
    assert report["sources"]["sms"]["missed"] == 0
    assert "unlabeled coverage" in report["sources"]["sms"]["interpretation"].lower()


def test_evaluation_markdown_is_concise_and_labels_limits():
    from backend.app.services.evaluation_report import render_markdown

    markdown = render_markdown({
        "total": 1,
        "sources": {"sms": {"total": 1, "detected": 1, "missed": 0, "labeled": 1, "unlabeled": 0}},
        "misses": [],
        "feature_coverage": {"credential_request": 1},
    })

    assert "offline" in markdown.lower()
    assert "not proof of safety" in markdown.lower()
    assert "credential_request" in markdown
