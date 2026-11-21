from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ReputationLookup:
    matched: bool
    source: str
    details: str | None = None


class ReputationProvider(Protocol):
    def lookup(self, url: str) -> ReputationLookup:
        """Look up a validated URL without fetching its page."""
