import json
from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from backend.app.repositories.website_cache_repository import normalize_cache_url

Connect = Callable[[str], Any]


class WebsiteGraphRepository:
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
        return self._connect(self._database_url)

    def _ensure_schema(self, cursor) -> None:
        if self._schema_ready:
            return
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scamguard_websites (
                normalized_url TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                expires_at TIMESTAMPTZ,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scamguard_website_links (
                source_url TEXT NOT NULL,
                target_url TEXT NOT NULL,
                payload JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (source_url, target_url)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS scamguard_website_analyses (
                normalized_url TEXT PRIMARY KEY,
                payload JSONB NOT NULL,
                updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            )
            """
        )
        self._schema_ready = True

    def _execute(self, statement: str, params: tuple) -> None:
        connection = self._open()
        try:
            cursor = connection.cursor()
            self._ensure_schema(cursor)
            cursor.execute(statement, params)
            connection.commit()
            cursor.close()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def save_website(self, raw_url: str, payload: dict, *, expires_at: datetime | None = None) -> None:
        url = normalize_cache_url(raw_url)
        self._execute(
            """
            INSERT INTO scamguard_websites (normalized_url, payload, expires_at, updated_at)
            VALUES (%s, %s::jsonb, %s, NOW())
            ON CONFLICT (normalized_url) DO UPDATE SET payload = EXCLUDED.payload,
            expires_at = EXCLUDED.expires_at, updated_at = NOW()
            """,
            (url, json.dumps(payload), expires_at),
        )

    def save_link(self, source_url: str, payload: dict) -> None:
        source = normalize_cache_url(source_url)
        target = normalize_cache_url(str(payload.get("url", "")))
        stored = {**payload, "url": target}
        self._execute(
            """
            INSERT INTO scamguard_website_links (source_url, target_url, payload, updated_at)
            VALUES (%s, %s, %s::jsonb, NOW())
            ON CONFLICT (source_url, target_url) DO UPDATE SET payload = EXCLUDED.payload,
            updated_at = NOW()
            """,
            (source, target, json.dumps(stored)),
        )

    def save_analysis(self, raw_url: str, payload: dict) -> None:
        self._execute(
            """
            INSERT INTO scamguard_website_analyses (normalized_url, payload, updated_at)
            VALUES (%s, %s::jsonb, NOW())
            ON CONFLICT (normalized_url) DO UPDATE SET payload = EXCLUDED.payload,
            updated_at = NOW()
            """,
            (normalize_cache_url(raw_url), json.dumps(payload)),
        )
