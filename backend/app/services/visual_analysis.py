from dataclasses import dataclass, field

from backend.app.adapters.gemini_visual import GeminiVisualAnalyzer, VisualAnalysis
from backend.app.services.browser_snapshot import BrowserSnapshot


@dataclass(frozen=True)
class VisualAnalysisResult:
    status: str
    site_type: str = "unknown"
    detected_brands: list[str] = field(default_factory=list)
    forms: list = field(default_factory=list)
    indicators: list = field(default_factory=list)
    sensitive_data_requested: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    screenshot_url: str | None = None
    model_name: str | None = None


class VisualAnalysisService:
    def __init__(self, analyzer: GeminiVisualAnalyzer | None) -> None:
        self.analyzer = analyzer

    def analyze(
        self,
        snapshot: BrowserSnapshot,
        *,
        claimed_brands: list[str] | None = None,
        deterministic_context: str = "",
    ) -> VisualAnalysisResult:
        if self.analyzer is None:
            return VisualAnalysisResult(
                status="unavailable",
                limitations=["Visual Gemini analysis is not configured."],
            )
        context = self._build_context(snapshot, claimed_brands or [], deterministic_context)
        try:
            analysis: VisualAnalysis = self.analyzer.analyze(
                snapshot.screenshot_bytes,
                mime_type="image/png",
                context=context,
            )
        except Exception:
            return VisualAnalysisResult(
                status="degraded",
                limitations=["Visual Gemini analysis failed; deterministic website evidence remains available."],
                model_name=getattr(self.analyzer, "model_name", None),
            )
        return VisualAnalysisResult(
            status=analysis.status,
            site_type=analysis.site_type,
            detected_brands=analysis.detected_brands,
            forms=analysis.forms,
            indicators=analysis.indicators,
            sensitive_data_requested=analysis.sensitive_data_requested,
            limitations=analysis.limitations + [
                "Visual similarity alone is not proof of phishing; combine with domain, HTML, links, and reputation evidence."
            ],
            model_name=getattr(self.analyzer, "model_name", None),
        )

    @staticmethod
    def _build_context(snapshot: BrowserSnapshot, brands: list[str], deterministic_context: str) -> str:
        return (
            f"Page title: {snapshot.title[:500]}\n"
            f"Final URL: {snapshot.final_url[:1000]}\n"
            f"Claimed brands: {', '.join(brands[:20]) or 'none'}\n"
            f"Deterministic evidence: {deterministic_context[:2000]}"
        )
