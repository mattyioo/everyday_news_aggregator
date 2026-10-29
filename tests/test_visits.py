from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from everyday_news import db
from everyday_news.visits import baseline, record_digest

T0 = datetime(2026, 10, 29, 8, 0, tzinfo=UTC)
H = timedelta(hours=1)


@pytest.fixture
def conn(tmp_path: Path):
    c = db.connect(tmp_path / "news.db")
    yield c
    c.close()


def fetched(conn, at: datetime) -> None:
    conn.execute(
        "INSERT INTO fetch_state (source_id, last_fetched_at, last_status) VALUES ('hn', ?, '200')"
        " ON CONFLICT (source_id) DO UPDATE SET last_fetched_at = excluded.last_fetched_at",
        (at.isoformat(),),
    )


def test_first_digest_has_no_baseline(conn) -> None:
    assert baseline(conn) is None
    fetched(conn, T0)
    assert baseline(conn) is None


def test_baseline_is_last_digest_before_latest_fetch(conn) -> None:
    fetched(conn, T0)
    record_digest(conn, T0 + 0.1 * H)  # visit 1: run = fetch + digest
    fetched(conn, T0 + 5 * H)
    record_digest(conn, T0 + 5.1 * H)  # visit 2
    assert baseline(conn) == T0 + 0.1 * H

    # Rewriting the digest without a new fetch keeps the same baseline
    record_digest(conn, T0 + 5.2 * H)
    assert baseline(conn) == T0 + 0.1 * H

    fetched(conn, T0 + 9 * H)  # visit 3
    assert baseline(conn) == T0 + 5.2 * H
