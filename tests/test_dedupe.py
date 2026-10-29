import sqlite3
from pathlib import Path

import pytest

from everyday_news import db
from everyday_news.dedupe import mark_duplicates
from everyday_news.normalize import title_hash
from everyday_news.sources import Source

SOURCES = [
    Source(id="bbc", name="BBC", url="https://bbc.example/feed", lang="en", weight=1.0),
    Source(id="hn", name="HN", url="https://hn.example/feed", lang="en", weight=0.9),
    Source(id="wp", name="WP", url="https://wp.example/feed", lang="pl", weight=0.7),
]


@pytest.fixture
def conn(tmp_path: Path):
    c = db.connect(tmp_path / "news.db")
    yield c
    c.close()


def add(conn, source_id, url, title, lang="en", published="2026-10-29T10:00:00+00:00") -> int:
    raw_id = conn.execute("SELECT COUNT(*) FROM article").fetchone()[0] + 1
    cursor = conn.execute(
        """
        INSERT INTO article (raw_item_id, source_id, lang, url, title, text, published_at,
                             title_hash)
        VALUES (?, ?, ?, ?, ?, '', ?, ?)
        """,
        (raw_id, source_id, lang, url, title, published, title_hash(title)),
    )
    return cursor.lastrowid


def duplicate_of(conn) -> dict[int, int | None]:
    return {r["id"]: r["duplicate_of"] for r in conn.execute("SELECT * FROM article")}


def test_same_url_across_sources_keeps_higher_weight_source(conn) -> None:
    hn = add(conn, "hn", "https://bbc.co.uk/news/1", "Train crash in Spain")
    bbc = add(conn, "bbc", "https://bbc.co.uk/news/1", "Spain train crash: what we know")
    assert mark_duplicates(conn, SOURCES) == 1
    assert duplicate_of(conn) == {hn: bbc, bbc: None}


def test_same_title_same_lang_is_duplicate(conn) -> None:
    first = add(
        conn, "wp", "https://wp.pl/a-1", "Pożar w Gdańsku", "pl", "2026-10-29T08:00:00+00:00"
    )
    again = add(
        conn, "wp", "https://wp.pl/a-2", "Pożar w Gdańsku!", "pl", "2026-10-29T09:00:00+00:00"
    )
    assert mark_duplicates(conn, SOURCES) == 1
    assert duplicate_of(conn) == {first: None, again: first}  # same weight: earliest wins


def test_same_title_different_lang_is_not_duplicate(conn) -> None:
    add(conn, "bbc", "https://bbc.co.uk/x", "Brexit", "en")
    add(conn, "wp", "https://wp.pl/x", "Brexit", "pl")
    assert mark_duplicates(conn, SOURCES) == 0


def test_url_and_title_matches_chain_into_one_group(conn) -> None:
    a = add(conn, "hn", "https://site/a", "Alpha")
    b = add(conn, "hn", "https://site/a", "Beta")  # same url as a
    c = add(conn, "bbc", "https://site/c", "Beta")  # same title as b
    assert mark_duplicates(conn, SOURCES) == 2
    assert duplicate_of(conn) == {a: c, b: c, c: None}


def test_idempotent_and_reassigns_when_better_primary_arrives(conn) -> None:
    hn = add(conn, "hn", "https://bbc.co.uk/news/2", "Story")
    assert mark_duplicates(conn, SOURCES) == 0
    assert mark_duplicates(conn, SOURCES) == 0

    bbc = add(conn, "bbc", "https://bbc.co.uk/news/2", "Story (BBC)")
    assert mark_duplicates(conn, SOURCES) == 1
    assert mark_duplicates(conn, SOURCES) == 1
    assert duplicate_of(conn) == {hn: bbc, bbc: None}


def test_unconfigured_source_loses_to_configured(conn) -> None:
    old = add(
        conn, "reddit-technology", "https://x/1", "Old", published="2026-10-28T00:00:00+00:00"
    )
    hn = add(conn, "hn", "https://x/1", "New")
    mark_duplicates(conn, SOURCES)
    assert duplicate_of(conn) == {old: hn, hn: None}


def test_old_database_is_migrated_in_place(tmp_path: Path) -> None:
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript(db.SCHEMA)  # schema as of 0004, user_version 0
    old.execute(
        "INSERT INTO article (raw_item_id, source_id, lang, url, title, text, published_at,"
        " title_hash) VALUES (1, 'hn', 'en', 'https://x', 'T', '', '2026-10-29', 'h')"
    )
    old.commit()
    old.close()

    conn = db.connect(path)
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
    row = conn.execute("SELECT title, duplicate_of FROM article").fetchone()
    assert (row["title"], row["duplicate_of"]) == ("T", None)
    conn.close()

    # Reopening doesn't re-run migrations
    db.connect(path).close()
