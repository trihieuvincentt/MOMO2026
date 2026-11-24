from collections.abc import Callable
from typing import Any

from backend.app.schemas.case import Case


Connect = Callable[[str], Any]


class PostgresCaseRepository:
    """PostgreSQL-backed case store; payloads are validated Pydantic JSON."""

    def __init__(self, database_url: str, *, connect: Connect | None = None) -> None:
        if not database_url or not database_url.strip():
            raise ValueError("Database URL is required")
        self._database_url = database_url.strip()
        self._connect = connect or self._default_connect
        self._schema_ready = False

    def _open_connection(self):
        try:
            return self._connect(self._database_url)
        except ModuleNotFoundError as exc:
            if exc.name == "psycopg":
                raise RuntimeError(
                    "PostgreSQL persistence is configured but the psycopg dependency is missing; install project dependencies."
                ) from exc
            raise

    @staticmethod
    def _default_connect(database_url: str):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError(
                "PostgreSQL persistence is configured but the psycopg dependency is missing; install project dependencies."
            ) from exc
        try:
            return psycopg.connect(database_url, connect_timeout=5)
        except Exception as exc:
            raise RuntimeError("PostgreSQL database connection failed.") from exc

    def _ensure_schema(self, cursor) -> None:
        if self._schema_ready:
            return
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scamguard_cases (
                case_id TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        self._schema_ready = True

    def save(self, case: Case) -> None:
        connection = self._open_connection()
        try:
            cursor = connection.cursor()
            self._ensure_schema(cursor)
            cursor.execute(
                """
                INSERT INTO scamguard_cases (case_id, payload, updated_at)
                VALUES (%s, %s::jsonb, NOW())
                ON CONFLICT (case_id) DO UPDATE
                SET payload = EXCLUDED.payload, updated_at = NOW()
                """,
                (case.id, case.model_dump_json()),
            )
            connection.commit()
            cursor.close()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get(self, case_id: str) -> Case:
        connection = self._open_connection()
        try:
            cursor = connection.cursor()
            self._ensure_schema(cursor)
            cursor.execute(
                "SELECT payload FROM scamguard_cases WHERE case_id = %s",
                (case_id,),
            )
            row = cursor.fetchone()
            cursor.close()
            if row is None:
                raise KeyError(case_id)
            payload = row[0]
            if isinstance(payload, str):
                return Case.model_validate_json(payload)
            return Case.model_validate(payload)
        finally:
            connection.close()

    def list_cases(self) -> list[Case]:
        connection = self._open_connection()
        try:
            cursor = connection.cursor()
            self._ensure_schema(cursor)
            cursor.execute("SELECT payload FROM scamguard_cases")
            rows = cursor.fetchall()
            cursor.close()
            cases = []
            for (payload,) in rows:
                cases.append(Case.model_validate_json(payload) if isinstance(payload, str) else Case.model_validate(payload))
            return cases
        finally:
            connection.close()
