from datetime import datetime, timedelta, timezone

from backend.app.repositories.website_cache_repository import WebsiteCacheRepository


class FakeCursor:
    def __init__(self, state):
        self.state = state
        self.result = None
        self.statements = []

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if "CREATE TABLE" in sql:
            return
        if "INSERT INTO scamguard_websites" in sql:
            url, payload, expires_at = params
            self.state[url] = {"payload": payload, "expires_at": expires_at}
        elif "SELECT payload, expires_at" in sql:
            row = self.state.get(params[0])
            self.result = (row["payload"], row["expires_at"]) if row else None
        elif "DELETE FROM scamguard_websites" in sql:
            self.state.clear()

    def fetchone(self):
        return self.result

    def close(self):
        pass


class FakeConnection:
    def __init__(self, state):
        self.cursor_instance = FakeCursor(state)

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


def test_website_cache_reuses_unexpired_analysis():
    state = {}
    repository = WebsiteCacheRepository("postgresql://fake", connect=lambda _: FakeConnection(state))
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    repository.save("https://example.com/", {"risk": "low"}, expires_at=expires)

    cached = repository.get("https://example.com/")

    assert cached is not None
    assert cached.payload == {"risk": "low"}
    assert cached.expires_at == expires


def test_website_cache_misses_expired_analysis():
    state = {}
    repository = WebsiteCacheRepository("postgresql://fake", connect=lambda _: FakeConnection(state))
    repository.save("https://example.com/", {"risk": "low"}, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))

    assert repository.get("https://example.com/") is None


def test_website_cache_cleanup_removes_expired_rows():
    state = {}
    repository = WebsiteCacheRepository("postgresql://fake", connect=lambda _: FakeConnection(state))
    repository.save("https://example.com/", {}, expires_at=datetime.now(timezone.utc) - timedelta(seconds=1))

    repository.cleanup_expired()

    assert state == {}
