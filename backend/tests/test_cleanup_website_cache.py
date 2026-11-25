import logging

from backend.app.jobs.cleanup_website_cache import main, run_cleanup


def test_run_cleanup_requires_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert run_cleanup() is False


def test_run_cleanup_invokes_cache_cleanup_once():
    calls = []

    class FakeCache:
        def cleanup(self):
            calls.append("cleanup")

    def factory(database_url):
        assert database_url == "postgresql://staging"
        return FakeCache()

    assert run_cleanup("postgresql://staging", cache_factory=factory) is True
    assert calls == ["cleanup"]


def test_run_cleanup_sanitizes_failure_logs(caplog):
    secret_dsn = "postgresql://user:password@example.test/db"

    def factory(_):
        raise RuntimeError(secret_dsn)

    with caplog.at_level(logging.ERROR):
        assert run_cleanup(secret_dsn, cache_factory=factory) is False

    assert "website cache cleanup failed" in caplog.text
    assert secret_dsn not in caplog.text
    assert "password" not in caplog.text


def test_main_maps_cleanup_result_to_exit_status(monkeypatch):
    monkeypatch.setattr(
        "backend.app.jobs.cleanup_website_cache.run_cleanup",
        lambda: True,
    )
    assert main() == 0

    monkeypatch.setattr(
        "backend.app.jobs.cleanup_website_cache.run_cleanup",
        lambda: False,
    )
    assert main() == 1
