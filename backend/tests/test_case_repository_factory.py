from backend.app.api.routes.cases import get_case_repository
from backend.app.repositories.case_repository import PostgresCaseRepository
from backend.app.services.case_service import InMemoryCaseRepository


def test_repository_factory_uses_memory_without_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert isinstance(get_case_repository(), InMemoryCaseRepository)


def test_repository_factory_uses_postgres_with_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://configured")

    assert isinstance(get_case_repository(), PostgresCaseRepository)
