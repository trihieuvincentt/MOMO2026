import base64
import json
from collections.abc import Callable

from backend.app.adapters.gemini import _http_transport
from backend.app.schemas.ocr import OCRSource


class GeminiVisionExtractor:
    def __init__(
        self,
        api_key: str,
        *,
        model_name: str = "gemini-3.8-flash",
        timeout_seconds: float = 15.0,
        transport: Callable[[str, str, dict[str, str], bytes, float], tuple[int, bytes]] = _http_transport,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("Gemini API key is required")
        self._api_key = api_key.strip()
        self._model_name = model_name
        self.model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def extract(self, image_bytes: bytes, language_hint: str | None = None):
        from types import SimpleNamespace

        instruction = (
            "Extract only the visible text from this image. Do not assess or classify the image. "
            "Return JSON with keys text and warnings. Mark unreadable portions in warnings. "
            f"Language hint: {language_hint or 'auto-detect'}."
        )
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model_name}:generateContent?key={self._api_key}"
        )
        body = json.dumps(
            {
                "contents": [{"parts": [
                    {"text": instruction},
                    {"inline_data": {"mime_type": "image/png", "data": base64.b64encode(image_bytes).decode()}},
                ]}],
                "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
            }
        ).encode()
        status, response_body = self._transport(
            "POST", url,
            {"Content-Type": "application/json", "Accept": "application/json"},
            body,
            self._timeout_seconds,
        )
        if status >= 400:
            raise RuntimeError(f"Gemini Vision provider returned HTTP {status}")
        try:
            payload = json.loads(response_body)
            text_output = payload["candidates"][0]["content"]["parts"][0]["text"]
            result = json.loads(text_output)
            extracted_text = result["text"]
            warnings = result.get("warnings", [])
        except (TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise ValueError("Gemini Vision OCR response was malformed") from exc
        if not isinstance(extracted_text, str):
            raise ValueError("Gemini Vision OCR response was malformed")
        if not extracted_text.strip() and not warnings:
            warnings = ["Image text was unreadable or uncertain."]
        return SimpleNamespace(
            text=extracted_text,
            warnings=[str(item) for item in warnings],
            ocr_source=OCRSource.GEMINI_VISION,
            provider_notice="This image was sent to Gemini for text extraction only.",
        )
