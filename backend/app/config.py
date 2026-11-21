import os

from dotenv import load_dotenv

from backend.app.adapters.reputation import GoogleWebRiskProvider, ReputationProvider

load_dotenv()


def get_reputation_provider() -> ReputationProvider | None:
    provider_name = os.getenv("REPUTATION_PROVIDER", "google_web_risk").strip().lower()
    api_key = os.getenv("GOOGLE_WEB_RISK_API_KEY", "")
    if provider_name != "google_web_risk" or not api_key.strip():
        return None
    return GoogleWebRiskProvider(api_key)
