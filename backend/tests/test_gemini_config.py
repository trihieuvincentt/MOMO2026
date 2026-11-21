from backend.app.adapters.gemini import GeminiInvestigationModel
from backend.app.config import get_investigation_model


def test_gemini_model_is_disabled_without_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    assert get_investigation_model() is None


def test_gemini_model_uses_server_side_key_and_configured_model(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "configured-gemini-key")
    monkeypatch.setenv("GEMINI_ENABLED", "true")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-3.8-flash")

    model = get_investigation_model()

    assert isinstance(model, GeminiInvestigationModel)
    assert model.model_name == "gemini-3.8-flash"
