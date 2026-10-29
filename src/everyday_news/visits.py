"""Remember when digests were written, to tell what is new since the last visit."""

import sqlite3
from datetime import datetime


def record_digest(conn: sqlite3.Connection, generated_at: datetime) -> None:
    conn.execute("INSERT INTO digest_run (generated_at) VALUES (?)", (generated_at.isoformat(),))
    conn.commit()


def baseline(conn: sqlite3.Connection) -> datetime | None:
    """The last digest written before the most recent fetch, or None for the first digest.

    Anchoring on the latest fetch keeps markers stable when the digest is rewritten
    without fetching (e.g. a relaunch inside the fetch cooldown).
    """
    last_fetch = conn.execute("SELECT MAX(last_fetched_at) FROM fetch_state").fetchone()[0]
    if last_fetch is None:
        row = conn.execute("SELECT MAX(generated_at) FROM digest_run").fetchone()
    else:
        row = conn.execute(
            "SELECT MAX(generated_at) FROM digest_run WHERE generated_at < ?", (last_fetch,)
        ).fetchone()
    return datetime.fromisoformat(row[0]) if row[0] else None
