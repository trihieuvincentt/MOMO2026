from backend.app.repositories.case_repository import PostgresCaseRepository


def test_postgres_repository_fails_with_actionable_error_when_driver_missing(monkeypatch):
    def missing_driver(database_url):
        raise ModuleNotFoundError("No module named 'psycopg'", name="psycopg")

    repository = PostgresCaseRepository("postgresql://configured", connect=missing_driver)

    try:
        repository.get("case-1")
    except RuntimeError as exc:
        assert "psycopg" in str(exc).lower()
        assert "dependency" in str(exc).lower()
    else:
        raise AssertionError("missing database driver should be reported clearly")
