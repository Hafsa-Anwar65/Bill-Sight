"""SQLite storage for user accounts, sessions and saved bills (stdlib only)."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS sessions (
    token_hash  TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at  TEXT    NOT NULL
);
CREATE TABLE IF NOT EXISTS bills (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_hash  TEXT    NOT NULL,
    bill_id     TEXT    NOT NULL,
    provider    TEXT,
    bill_month  TEXT,
    units       REAL,
    payable     REAL,
    data        TEXT    NOT NULL,
    saved_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    UNIQUE (user_id, image_hash)
);
CREATE INDEX IF NOT EXISTS bills_by_user ON bills (user_id, bill_month);
"""


def _connect() -> sqlite3.Connection:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


_ready: set[str] = set()


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = _connect()
    try:
        key = str(settings.db_path)
        if key not in _ready:
            conn.executescript(SCHEMA)
            _ready.add(key)
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
