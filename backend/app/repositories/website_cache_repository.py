import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

Connect = Callable[[str], Any]


@dataclass(frozen=True)
class CachedWebsite:
    normalized_url: str
    payload: dict
    expires_at: datetime


def normalize_cache_url(raw_url: str) -> str:
    value = raw_url.strip()
    parts = urlsplit(value)
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError("A valid http or https URL is required")
    hostname = parts.hostname.encode("idna").decode("ascii").lower()
    port = parts.port
    netloc = hostname if port is None else f"{hostname}:{port}"
    return urlunsplit((parts.scheme.lower(), netloc, parts.path or "/", parts.query, ""))


class WebsiteCacheRepository:
    def __init__(self, database_url: str, *, connect: Connect | None = None) -> None:
        if not database_url or not database_url.strip():
            raise ValueError("Database URL is required")
        self._database_url = database_url.strip()
        self._connect = connect or self._default_connect
        self._schema_ready = False

    @staticmethod
    def _default_connect(database_url: str):
        try:
            import psycopg
        except ImportError as exc:
            raise RuntimeError("PostgreSQL persistence requires the psycopg dependency") from exc
        return psycopg.connect(database_url, connect_timeout=5)

    def _open(self):
        try:
            return self._connect(self._database_url)
        except ModuleNotFoundError as exc:
            if exc.name == "psycopg":
                raise RuntimeError("PostgreSQL persistence requires the psycopg dependency") from exc
            raise

    def _ensure_schema(self, cursor) -> None:
        if self._schema_ready:
            return
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scamguard_websites (
                normalized_url TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                expires_at TIMESTAMPTZ NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS scamguard_websites_expires_idx
            ON scamguard_websites (expires_at)
            """
        )
        self._schema_ready = True

    def save(self, raw_url: str, payload: dict, *, expires_at: datetime) -> CachedWebsite:
        normalized_url = normalize_cache_url(raw_url)
        connection = self._open()
        try:
            cursor = connection.cursor()
            self._ensure_schema(cursor)
            cursor.execute(
                """
                INSERT INTO scamguard_websites (normalized_url, payload, expires_at, updated_at)
                VALUES (%s, %s::jsonb, %s, NOW())
                ON CONFLICT (normalized_url) DO UPDATE
                SET payload = EXCLUDED.payload, expires_at = EXCLUDED.expires_at, updated_at = NOW()
                """,
                (normalized_url, json.dumps(payload), expires_at),
            )
            connection.commit()
            cursor.close()
            return CachedWebsite(normalized_url, payload, expires_at)
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def get(self, raw_url: str, *, now: datetime | None = None) -> CachedWebsite | None:
        normalized_url = normalize_cache_url(raw_url)
        connection = self._open()
        try:
            cursor = connection.cursor()
            self._ensure_schema(cursor)
            cursor.execute(
                "SELECT payload, expires_at FROM scamguard_websites WHERE normalized_url = %s",
                (normalized_url,),
            )
            row = cursor.fetchone()
            cursor.close()
        finally:
            connection.close()
        if row is None:
            return None
        payload, expires_at = row
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        current = now or datetime.now(timezone.utc)
        if expires_at <= current:
            return None
        if isinstance(payload, str):
            payload = json.loads(payload)
        return CachedWebsite(normalized_url, payload, expires_at)

    def cleanup_expired(self, *, now: datetime | None = None) -> None:
        current = now or datetime.now(timezone.utc)
        connection = self._open()
        try:
            cursor = connection.cursor()
            self._ensure_schema(cursor)
            cursor.execute("DELETE FROM scamguard_websites WHERE expires_at <= %s", (current,))
            connection.commit()
            cursor.close()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
