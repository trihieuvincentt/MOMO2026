from dataclasses import dataclass

from backend.app.adapters.gemini_visual import VisualAnalysis, VisualForm, VisualIndicator
from backend.app.services.browser_snapshot import BrowserSnapshot
from backend.app.services.visual_analysis import VisualAnalysisService


@dataclass
class FakeAnalyzer:
    def analyze(self, image_bytes, *, mime_type, context=""):
        assert image_bytes == b"PNG"
        assert mime_type == "image/png"
        assert "Example Bank" in context
        return VisualAnalysis(
            site_type="banking",
            detected_brands=["Example Bank"],
            forms=[VisualForm("login", ["password"])],
            indicators=[VisualIndicator("sensitive_form", "Password field visible", 0.9)],
            sensitive_data_requested=["password"],
            limitations=[],
        )


def test_visual_service_combines_snapshot_and_deterministic_context():
    snapshot = BrowserSnapshot(
        requested_url="https://example.com",
        normalized_url="https://example.com/",
        final_url="https://example.com/",
        status_code=200,
        title="Example Bank Login",
        screenshot_bytes=b"PNG",
        html="<html />",
        redirect_chain=("https://example.com/",),
    )

    result = VisualAnalysisService(FakeAnalyzer()).analyze(
        snapshot,
        claimed_brands=["Example Bank"],
        deterministic_context="login form requests password",
    )

    assert result.status == "success"
    assert result.site_type == "banking"
    assert result.detected_brands == ["Example Bank"]
    assert result.screenshot_url is None


def test_visual_service_degrades_without_analyzer():
    snapshot = BrowserSnapshot(
        "https://example.com", "https://example.com/", "https://example.com/", 200,
        "Example", b"PNG", "<html />", ("https://example.com/",),
    )

    result = VisualAnalysisService(None).analyze(snapshot)

    assert result.status == "unavailable"
    assert "not configured" in " ".join(result.limitations).lower()
