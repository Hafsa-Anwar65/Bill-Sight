"""Storage for user accounts, sessions and saved bills.

Uses PostgreSQL when DATABASE_URL is set (for hosting, e.g. Vercel + Neon), otherwise a local
SQLite file. Queries are written once with `?` placeholders and work on both.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from .config import settings

SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash  TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS bills (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_hash  TEXT NOT NULL,
    bill_id     TEXT NOT NULL,
    provider    TEXT,
    bill_month  TEXT,
    units       REAL,
    payable     REAL,
    data        TEXT NOT NULL,
    saved_at    TEXT NOT NULL,
    UNIQUE (user_id, image_hash)
);
CREATE INDEX IF NOT EXISTS bills_by_user ON bills (user_id, bill_month);
"""

POSTGRES_SCHEMA = SQLITE_SCHEMA.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY").replace(
    "REAL", "DOUBLE PRECISION"
)


class Conn:
    """Tiny wrapper so the same `?`-style SQL runs on SQLite and PostgreSQL; rows come back as dicts."""

    def __init__(self, raw: Any, postgres: bool):
        self.raw = raw
        self.postgres = postgres

    def execute(self, sql: str, params: tuple = ()) -> Any:
        if self.postgres:
            sql = sql.replace("?", "%s")
        return self.raw.execute(sql, params)

    def one(self, sql: str, params: tuple = ()) -> dict[str, Any] | None:
        row = self.execute(sql, params).fetchone()
        return dict(row) if row is not None else None

    def all(self, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
        return [dict(r) for r in self.execute(sql, params).fetchall()]


_ready: set[str] = set()


def _open() -> tuple[Any, bool, str]:
    if settings.database_url:
        import psycopg
        from psycopg.rows import dict_row

        return psycopg.connect(settings.database_url, row_factory=dict_row, connect_timeout=10), True, settings.database_url
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    raw = sqlite3.connect(settings.db_path, timeout=10)
    raw.row_factory = sqlite3.Row
    raw.execute("PRAGMA foreign_keys = ON")
    return raw, False, str(settings.db_path)


@contextmanager
def connect() -> Iterator[Conn]:
    raw, postgres, key = _open()
    conn = Conn(raw, postgres)
    try:
        if key not in _ready:
            if postgres:
                for stmt in filter(str.strip, POSTGRES_SCHEMA.split(";")):
                    raw.execute(stmt)
            else:
                raw.executescript(SQLITE_SCHEMA)
            _ready.add(key)
        yield conn
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()
