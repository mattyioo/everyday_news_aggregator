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

CREATE TABLE IF NOT EXISTS article (
    id             INTEGER PRIMARY KEY,
    raw_item_id    INTEGER NOT NULL UNIQUE REFERENCES raw_item (id),
    source_id      TEXT NOT NULL,
    lang           TEXT NOT NULL,
    url            TEXT NOT NULL,
    discussion_url TEXT,
    title          TEXT NOT NULL,
    text           TEXT NOT NULL,
    published_at   TEXT NOT NULL,
    title_hash     TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS article_title_hash ON article (title_hash);
CREATE INDEX IF NOT EXISTS article_published_at ON article (published_at);
"""

# Changes to the schema above, applied in order to existing databases.
# Never edit or reorder an entry once committed; append a new one instead.
# `PRAGMA user_version` records how many have been applied.
MIGRATIONS = [
    # 1 (0006): exact duplicates point at the article that is shown instead
    "ALTER TABLE article ADD COLUMN duplicate_of INTEGER REFERENCES article (id);",
]


def connect(path: Path | str = DEFAULT_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn


def _migrate(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    for number, sql in enumerate(MIGRATIONS[version:], start=version + 1):
        conn.executescript(f"BEGIN; {sql} PRAGMA user_version = {number}; COMMIT;")
