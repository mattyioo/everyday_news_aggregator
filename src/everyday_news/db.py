"""SQLite database: one file, schema created on open."""

import sqlite3
from pathlib import Path

DEFAULT_PATH = Path("news.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS fetch_state (
    source_id       TEXT PRIMARY KEY,
    last_fetched_at TEXT NOT NULL,
    last_status     TEXT NOT NULL,
    etag            TEXT,
    last_modified   TEXT
);

CREATE TABLE IF NOT EXISTS raw_item (
    id           INTEGER PRIMARY KEY,
    source_id    TEXT NOT NULL,
    guid         TEXT NOT NULL,
    url          TEXT,
    title        TEXT,
    summary      TEXT,
    comments_url TEXT,
    published    TEXT,
    fetched_at   TEXT NOT NULL,
    UNIQUE (source_id, guid)
);
"""


def connect(path: Path | str = DEFAULT_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn
