import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from everyday_news import db
from everyday_news.fetch import fetch_all, make_client
from everyday_news.normalize import normalize_pending
from everyday_news.prune import prune
from everyday_news.settings import SettingsError, load_settings
from everyday_news.sources import Source

FIXTURES = Path(__file__).parent / "fixtures"
T0 = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)
DAY = timedelta(days=1)
WP = Source(id="wp", name="WP", url="https://wp.example/feed", lang="pl")


@pytest.fixture
def conn(tmp_path: Path):
    c = db.connect(tmp_path / "news.db")
    yield c
    c.close()


def fetch(conn, at: datetime, response: httpx.Response) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return response

    with make_client(httpx.MockTransport(handler)) as client:
        fetch_all([WP], conn, client, force=True, now=lambda: at, sleep=lambda s: None)
    normalize_pending(conn, [WP])


def feed() -> httpx.Response:
    return httpx.Response(200, content=(FIXTURES / "wp.xml").read_bytes())


def count(conn, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_items_unseen_for_retention_period_are_deleted(conn) -> None:
    fetch(conn, T0, feed())
    assert count(conn, "article") == 3

    assert prune(conn, [WP], 30, T0 + 29 * DAY) == 0
    assert prune(conn, [WP], 30, T0 + 30 * DAY + timedelta(seconds=1)) == 3
    assert (count(conn, "article"), count(conn, "raw_item")) == (0, 0)


def test_items_still_in_feed_are_kept_however_old(conn) -> None:
    fetch(conn, T0, feed())
    fetch(conn, T0 + 40 * DAY, feed())  # same items still listed
    assert prune(conn, [WP], 30, T0 + 41 * DAY) == 0
    assert count(conn, "article") == 3


def test_not_modified_counts_as_still_in_feed(conn) -> None:
    fetch(conn, T0, feed())
    fetch(conn, T0 + 20 * DAY, httpx.Response(304))
    assert prune(conn, [WP], 30, T0 + 45 * DAY) == 0
    assert prune(conn, [WP], 30, T0 + 51 * DAY) == 3


def test_failed_fetch_does_not_count_as_seen(conn) -> None:
    fetch(conn, T0, feed())
    fetch(conn, T0 + 20 * DAY, httpx.Response(503))
    assert prune(conn, [WP], 30, T0 + 31 * DAY) == 3


def test_only_items_that_left_the_feed_are_deleted(conn) -> None:
    fetch(conn, T0, feed())
    conn.execute(
        "INSERT INTO raw_item (source_id, guid, title, url, fetched_at, last_seen_at)"
        " VALUES ('wp', 'gone', 'Old', 'https://wp.pl/old', ?, ?)",
        ((T0 - 60 * DAY).isoformat(), (T0 - 60 * DAY).isoformat()),
    )
    normalize_pending(conn, [WP])
    assert count(conn, "article") == 4
    assert prune(conn, [WP], 30, T0) == 1
    assert conn.execute("SELECT guid FROM raw_item WHERE guid = 'gone'").fetchone() is None


def test_fetch_state_of_removed_sources_is_dropped(conn) -> None:
    fetch(conn, T0, feed())
    conn.execute(
        "INSERT INTO fetch_state (source_id, last_fetched_at, last_status)"
        " VALUES ('reddit-technology', ?, 'error')",
        (T0.isoformat(),),
    )
    prune(conn, [WP], 30, T0)
    assert [r[0] for r in conn.execute("SELECT source_id FROM fetch_state")] == ["wp"]


def test_migration_backfills_last_seen(tmp_path: Path) -> None:
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript(db.SCHEMA)
    old.execute(db.MIGRATIONS[0])
    old.execute("PRAGMA user_version = 1")
    old.execute(
        "INSERT INTO raw_item (source_id, guid, fetched_at) VALUES ('wp', 'g', '2026-10-01')"
    )
    old.commit()
    old.close()

    conn = db.connect(path)
    assert conn.execute("SELECT last_seen_at FROM raw_item").fetchone()[0] == "2026-10-01"
    assert conn.execute("PRAGMA user_version").fetchone()[0] == len(db.MIGRATIONS)
    conn.close()


def test_settings_file(tmp_path: Path) -> None:
    path = tmp_path / "settings.toml"
    path.write_text("retention_days = 7\n", encoding="utf-8")
    assert load_settings(path).retention_days == 7

    for bad in ("retention_days = 0", 'retention_days = "30"', "retention_days = 1.5"):
        path.write_text(bad + "\n", encoding="utf-8")
        with pytest.raises(SettingsError, match="retention_days must be"):
            load_settings(path)

    with pytest.raises(SettingsError, match="file not found"):
        load_settings(tmp_path / "missing.toml")


def test_project_settings_file_is_valid() -> None:
    assert load_settings(Path(__file__).parent.parent / "settings.toml").retention_days == 7
