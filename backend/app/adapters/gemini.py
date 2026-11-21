import json
import urllib.request
from collections.abc import Callable
from urllib.error import HTTPError, URLError


Transport = Callable[[str, str, dict[str, str], bytes, float], tuple[int, bytes]]


class GeminiProviderError(RuntimeError):
    """Gemini did not return a usable investigation response."""



def _http_transport(
    method: str,
    url: str,
    headers: dict[str, str],
    body: bytes,
    timeout: float,
) -> tuple[int, bytes]:
    request = urllib.request.Request(url, headers=headers, method=method, data=body)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            return int(response.status), response.read()
    except HTTPError as exc:
        return exc.code, exc.read()
    except URLError as exc:
        raise GeminiProviderError("Gemini network failure") from exc


class GeminiInvestigationModel:
    def __init__(
        self,
        api_key: str,
        *,
        model_name: str = "gemini-2.0-flash",
        timeout_seconds: float = 12.0,
        transport: Transport = _http_transport,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("Gemini API key is required")
        self._api_key = api_key.strip()
        self._model_name = model_name
        self.model_name = model_name
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def generate(self, prompt: str) -> object:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model_name}:generateContent?key={self._api_key}"
        )
        body = json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {
                    "temperature": 0.1,
                    "responseMimeType": "application/json",
                },
            }
        ).encode()
        try:
            status, response_body = self._transport(
                "POST",
                endpoint,
                {"Content-Type": "application/json", "Accept": "application/json"},
                body,
                self._timeout_seconds,
            )
        except TimeoutError as exc:
            raise GeminiProviderError("Gemini request timed out") from exc
        if status == 429 or status >= 500:
            raise GeminiProviderError(f"Gemini provider unavailable (HTTP {status})")
        if status >= 400:
            raise GeminiProviderError(f"Gemini request rejected (HTTP {status})")
        try:
            payload = json.loads(response_body)
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
        except (TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
            raise GeminiProviderError("Gemini response did not contain a candidate") from exc
        if not isinstance(text, str) or not text.strip():
            raise GeminiProviderError("Gemini response contained empty candidate text")
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise GeminiProviderError("Gemini candidate was not valid JSON") from exc
