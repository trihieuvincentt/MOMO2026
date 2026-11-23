import pytest

from backend.app.schemas.case import Case, EvidenceScanStatus
from backend.app.schemas.evidence import EvidenceItem, EvidenceType
from backend.app.schemas.finding import Finding, FindingSource, Severity, VerificationStatus
from backend.app.schemas.investigation import InvestigationStatus
from backend.app.services.investigation_engine import investigate_case


def make_case() -> Case:
    evidence = [
        EvidenceItem(id="e-message", type=EvidenceType.MESSAGE, content_reference="Pay a fee now"),
        EvidenceItem(id="e-url", type=EvidenceType.URL, content_reference="https://example.com/"),
    ]
    finding = Finding(
        id="f-fee",
        category="advance_fee",
        description="Upfront fee request",
        evidence_item_id="e-message",
        source_type=FindingSource.RULE,
        verification_status=VerificationStatus.SUSPICIOUS_INDICATOR,
        severity=Severity.HIGH,
    )
    return Case(
        id="case-test",
        evidence=evidence,
        findings=[finding],
        scanner_statuses={"e-message": EvidenceScanStatus.SUCCESS, "e-url": EvidenceScanStatus.SUCCESS},
    )


class ValidModel:
    def generate(self, prompt: str):
        return {
            "summary": "The message contains an advance-fee indicator.",
            "finding_explanations": [{"finding_id": "f-fee", "explanation": "The fee request is suspicious."}],
            "relationships": [],
            "unknowns": ["The URL has not been proven safe."],
        }


def test_investigation_interprets_findings_and_preserves_valid_references():
    result = investigate_case(make_case(), ValidModel())

    assert result.status == InvestigationStatus.SUCCESS
    assert result.finding_explanations[0].finding_id == "f-fee"
    assert result.unknowns


def test_unrelated_evidence_has_no_invented_relationship():
    class UnrelatedModel:
        def generate(self, prompt: str):
            return {
                "summary": "The items are unrelated based on supplied evidence.",
                "finding_explanations": [],
                "relationships": [],
                "unknowns": ["No supported relationship was established."],
            }

    result = investigate_case(make_case(), UnrelatedModel())

    assert result.relationships == []


def test_invalid_finding_reference_degrades_without_returning_invented_reference():
    class HallucinatingModel:
        def generate(self, prompt: str):
            return {
                "summary": "Unsupported claim.",
                "finding_explanations": [{"finding_id": "f-invented", "explanation": "made up"}],
                "relationships": [],
                "unknowns": [],
            }

    result = investigate_case(make_case(), HallucinatingModel())

    assert result.status == InvestigationStatus.DEGRADED
    assert result.finding_explanations == []
    assert any("reference" in item.lower() for item in result.unknowns)


@pytest.mark.parametrize("output", ["not json", {"summary": "missing fields"}])
def test_malformed_model_output_degrades_safely(output):
    class MalformedModel:
        def generate(self, prompt: str):
            return output

    result = investigate_case(make_case(), MalformedModel())

    assert result.status == InvestigationStatus.DEGRADED
    assert result.finding_explanations == []


def test_provider_timeout_returns_rule_only_degraded_result():
    class TimeoutModel:
        def generate(self, prompt: str):
            raise TimeoutError("timeout")

    result = investigate_case(make_case(), TimeoutModel())

    assert result.status == InvestigationStatus.DEGRADED
    assert "rule" in result.summary.lower()
    assert result.finding_explanations == []


def test_provider_failure_logs_diagnostics_without_prompt_or_sensitive_evidence(caplog):
    api_key = "secret-api-key"

    class FailingModel:
        model_name = "gemini-test-model"

        def generate(self, prompt: str):
            raise RuntimeError(f"provider rejected request for {api_key}: {prompt}")

    with caplog.at_level("WARNING", logger="backend.app.services.investigation_engine"):
        result = investigate_case(make_case(), FailingModel())

    assert result.status == InvestigationStatus.DEGRADED
    assert "Gemini investigation degraded" in caplog.text
    assert "RuntimeError" in caplog.text
    assert "gemini-test-model" in caplog.text
    assert api_key not in caplog.text
    assert "Pay a fee now" not in caplog.text
    assert "https://example.com/" not in caplog.text
