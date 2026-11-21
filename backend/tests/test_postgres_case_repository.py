import json

from backend.app.schemas.case import Case
from backend.app.repositories.case_repository import PostgresCaseRepository


class FakeCursor:
    def __init__(self, state):
        self.state = state
        self.result = None
        self.statements = []

    def execute(self, sql, params=None):
        self.statements.append((sql, params))
        if "CREATE TABLE" in sql:
            return
        if "INSERT INTO scamguard_cases" in sql:
            case_id, payload = params
            self.state[case_id] = payload
        elif "SELECT payload" in sql:
            self.result = self.state.get(params[0])

    def fetchone(self):
        return (self.result,) if self.result is not None else None

    def close(self):
        pass


class FakeConnection:
    def __init__(self, state):
        self.state = state
        self.cursor_instance = FakeCursor(state)

    def cursor(self):
        return self.cursor_instance

    def commit(self):
        pass

    def close(self):
        pass


def test_case_survives_repository_recreation():
    state = {}
    repository = PostgresCaseRepository("postgresql://fake", connect=lambda _: FakeConnection(state))
    original = Case(id="case-persist", summary="persist me")

    repository.save(original)
    restarted_repository = PostgresCaseRepository("postgresql://fake", connect=lambda _: FakeConnection(state))
    restored = restarted_repository.get("case-persist")

    assert restored.id == original.id
    assert restored.summary == "persist me"


def test_postgres_repository_uses_parameterized_upsert_and_json_payload():
    state = {}
    connection = FakeConnection(state)
    repository = PostgresCaseRepository("postgresql://fake", connect=lambda _: connection)

    repository.save(Case(id="case-safe", summary="sample"))

    insert = next(statement for statement in connection.cursor_instance.statements if "INSERT INTO scamguard_cases" in statement[0])
    assert "%s" in insert[0]
    assert insert[1][0] == "case-safe"
    assert json.loads(insert[1][1])["summary"] == "sample"


def test_missing_case_raises_key_error():
    repository = PostgresCaseRepository("postgresql://fake", connect=lambda _: FakeConnection({}))

    try:
        repository.get("case-missing")
    except KeyError as exc:
        assert str(exc).strip("'\"") == "case-missing"
    else:
        raise AssertionError("missing case must raise KeyError")
