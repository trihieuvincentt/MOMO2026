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


def test_evaluation_markdown_is_concise_and_labels_limits():
    from backend.app.services.evaluation_report import render_markdown

    markdown = render_markdown({
        "total": 1,
        "sources": {"sms": {"total": 1, "detected": 1, "missed": 0}},
        "misses": [],
        "feature_coverage": {"credential_request": 1},
    })

    assert "offline" in markdown.lower()
    assert "not proof of safety" in markdown.lower()
    assert "credential_request" in markdown
