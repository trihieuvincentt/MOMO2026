import os

from dotenv import load_dotenv

from backend.app.adapters.reputation import (
    MultiSourceReputationProvider,
    ReputationProvider,
    URLhausProvider,
    VirusTotalProvider,
)

load_dotenv()


def get_reputation_provider() -> ReputationProvider | None:
    provider_name = os.getenv("REPUTATION_PROVIDER", "virus_total_urlhaus").strip().lower()
    if provider_name not in {"virus_total_urlhaus", "multi_source", "google_web_risk"}:
        return None

    providers: list[ReputationProvider] = []
    virustotal_key = os.getenv("VIRUSTOTAL_API_KEY", "")
    urlhaus_key = os.getenv("URLHAUS_API_KEY", "") or os.getenv("URLHAUS_AUTH_KEY", "")
    if virustotal_key.strip():
        providers.append(VirusTotalProvider(virustotal_key))
    if urlhaus_key.strip():
        providers.append(URLhausProvider(urlhaus_key))
    return MultiSourceReputationProvider(providers) if providers else None
