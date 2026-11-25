import base64
import json
from collections.abc import Callable
from dataclasses import dataclass, field

from backend.app.adapters.gemini import GeminiProviderError, _http_transport


@dataclass(frozen=True)
class VisualIndicator:
    category: str
    description: str
    confidence: float
    evidence: str | None = None


@dataclass(frozen=True)
class VisualForm:
    purpose: str
    fields: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class VisualAnalysis:
    site_type: str
    detected_brands: list[str]
    forms: list[VisualForm]
    indicators: list[VisualIndicator]
    sensitive_data_requested: list[str]
    limitations: list[str]
    status: str = "success"


class GeminiVisualAnalyzer:
    def __init__(
        self,
        api_key: str,
        *,
        model_name: str = "gemini-3.8-flash",
        timeout_seconds: float = 20.0,
        transport: Callable = _http_transport,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("Gemini API key is required")
        self._api_key = api_key.strip()
        self._model_name = model_name
        self.model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def analyze(
        self,
        image_bytes: bytes,
        *,
        mime_type: str = "image/png",
        context: str = "",
    ) -> VisualAnalysis:
        if mime_type not in {"image/png", "image/jpeg"}:
            raise ValueError("Visual analysis supports PNG and JPEG images only")
        if not image_bytes:
            raise ValueError("Visual analysis image is empty")
        instruction = self._instruction(context)
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model_name}:generateContent?key={self._api_key}"
        )
        body = json.dumps({
            "contents": [{"parts": [
                {"text": instruction},
                {"inline_data": {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode("ascii")}},
            ]}],
            "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
        }).encode()
        try:
            status, response_body = self._transport(
                "POST", endpoint,
                {"Content-Type": "application/json", "Accept": "application/json"},
                body, self._timeout_seconds,
            )
        except TimeoutError as exc:
            raise GeminiProviderError("Gemini visual analysis timed out") from exc
        if status == 429 or status >= 500:
            raise GeminiProviderError(f"Gemini visual provider unavailable (HTTP {status})")
        if status >= 400:
            raise GeminiProviderError(f"Gemini visual request rejected (HTTP {status})")
        payload = self._parse_payload(response_body)
        return self._validate_result(payload)

    @staticmethod
    def _instruction(context: str) -> str:
        return (
            "Analyze only visible website interface evidence in this screenshot. "
            "Return JSON matching the requested fields. Identify site_type, visible brands, "
            "forms and fields, sensitive data requested, and visual indicators. "
            "Do not declare the website definitively phishing based on appearance alone. "
            "Every indicator must describe visible evidence and have confidence from 0 to 1. "
            "Allowed indicator categories include brand_impersonation, sensitive_form, visual_mismatch, "
            "credential_collection, suspicious_claim, and unusual_redirect. "
            "Use an empty array when uncertain. Context from deterministic analysis follows: "
            + context[:4000]
        )

    @staticmethod
    def _parse_payload(response_body: bytes) -> dict:
        try:
            payload = json.loads(response_body)
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip())
        except (TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise RuntimeError("Gemini visual response was not structured JSON") from exc
        if not isinstance(result, dict):
            raise RuntimeError("Gemini visual response was not structured JSON")
        return result

    @staticmethod
    def _validate_result(payload: dict) -> VisualAnalysis:
        indicators: list[VisualIndicator] = []
        for item in payload.get("indicators", []):
            if not isinstance(item, dict) or not item.get("category") or not item.get("description"):
                continue
            try:
                confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0))))
            except (TypeError, ValueError):
                confidence = 0.0
            indicators.append(VisualIndicator(
                category=str(item["category"]),
                description=str(item["description"]),
                confidence=confidence,
                evidence=str(item["evidence"]) if item.get("evidence") else None,
            ))
        forms = [
            VisualForm(str(item.get("purpose", "unknown")), [str(field) for field in item.get("fields", [])])
            for item in payload.get("forms", [])
            if isinstance(item, dict)
        ]
        return VisualAnalysis(
            site_type=str(payload.get("site_type", "unknown")),
            detected_brands=[str(item) for item in payload.get("detected_brands", [])],
            forms=forms,
            indicators=indicators,
            sensitive_data_requested=[str(item) for item in payload.get("sensitive_data_requested", [])],
            limitations=[str(item) for item in payload.get("limitations", [])],
        )
