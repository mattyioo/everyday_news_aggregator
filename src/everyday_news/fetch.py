"""Fetch feeds politely: once per run, one request per source, no retries.

Rules (see context/foundation/decisions.md):
- honest User-Agent, sequential requests with a pause between them
- conditional GET (ETag / Last-Modified) so unchanged feeds cost ~nothing
- cooldown: a source fetched recently is skipped entirely
- 429 / 5xx / network errors skip the source for this run, never retry,
  and back off for longer than the normal cooldown
"""

import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import feedparser
import httpx

from everyday_news import __version__
from everyday_news.sources import Source

USER_AGENT = f"everyday_news/{__version__} (personal news reader; one fetch per launch)"
TIMEOUT = 15.0
PAUSE_SECONDS = 2.0
COOLDOWN = timedelta(minutes=15)
ERROR_COOLDOWN = timedelta(minutes=60)


@dataclass(frozen=True)
class FetchResult:
    source_id: str
    status: str  # "200", "304", "skipped", "error"
    detail: str
    requested: bool  # whether an HTTP request was sent


def make_client(transport: httpx.BaseTransport | None = None) -> httpx.Client:
    # No automatic redirects: a redirect is a second request. Feed URLs in
    # sources.toml should point at the final location.
    return httpx.Client(
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
        follow_redirects=False,
        transport=transport,
    )


def fetch_all(
    sources: list[Source],
    conn: sqlite3.Connection,
    client: httpx.Client,
    *,
    force: bool = False,
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
    sleep: Callable[[float], None] = time.sleep,
) -> list[FetchResult]:
    """Fetch every enabled source once. Never raises for a single source's failure."""
    results = []
    for source in sources:
        if not source.enabled:
            results.append(FetchResult(source.id, "skipped", "disabled", requested=False))
            continue

        state = conn.execute(
            "SELECT * FROM fetch_state WHERE source_id = ?", (source.id,)
        ).fetchone()
        if state and not force:
            cooldown = ERROR_COOLDOWN if state["last_status"] == "error" else COOLDOWN
            age = now() - datetime.fromisoformat(state["last_fetched_at"])
            if age < cooldown:
                minutes = int((cooldown - age).total_seconds() // 60) + 1
                reason = "backoff after error" if cooldown == ERROR_COOLDOWN else "cooldown"
                results.append(
                    FetchResult(
                        source.id, "skipped", f"{reason} ({minutes} min left)", requested=False
                    )
                )
                continue

        if any(r.requested for r in results):
            sleep(PAUSE_SECONDS)
        results.append(_fetch_one(source, state, conn, client, now()))
        conn.commit()
    return results


def _fetch_one(
    source: Source,
    state: sqlite3.Row | None,
    conn: sqlite3.Connection,
    client: httpx.Client,
    fetched_at: datetime,
) -> FetchResult:
    headers = {}
    if state and state["etag"]:
        headers["If-None-Match"] = state["etag"]
    if state and state["last_modified"]:
        headers["If-Modified-Since"] = state["last_modified"]

    etag = state["etag"] if state else None
    last_modified = state["last_modified"] if state else None

    try:
        response = client.get(source.url, headers=headers)
    except httpx.HTTPError as e:
        result = FetchResult(source.id, "error", type(e).__name__, requested=True)
    else:
        code = response.status_code
        if code == 304:
            result = FetchResult(source.id, "304", "not modified", requested=True)
        elif code == 200:
            etag = response.headers.get("etag")
            last_modified = response.headers.get("last-modified")
            total, new = _store_items(source, response.content, conn, fetched_at)
            result = FetchResult(source.id, "200", f"{total} items ({new} new)", requested=True)
        else:
            result = FetchResult(source.id, "error", f"HTTP {code}", requested=True)

    # Every attempt counts toward the cooldown, failures included: a site
    # that answered 429 should not hear from us again on the next launch.
    conn.execute(
        """
        INSERT INTO fetch_state (source_id, last_fetched_at, last_status, etag, last_modified)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT (source_id) DO UPDATE SET
            last_fetched_at = excluded.last_fetched_at,
            last_status = excluded.last_status,
            etag = excluded.etag,
            last_modified = excluded.last_modified
        """,
        (source.id, fetched_at.isoformat(), result.status, etag, last_modified),
    )
    return result


def _store_items(
    source: Source, content: bytes, conn: sqlite3.Connection, fetched_at: datetime
) -> tuple[int, int]:
    """Insert parsed entries, skipping ones already stored. Returns (total, new)."""
    feed = feedparser.parse(content)
    new = 0
    for entry in feed.entries:
        guid = entry.get("id") or entry.get("link")
        if not guid:
            continue
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO raw_item
                (source_id, guid, url, title, summary, comments_url, published, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source.id,
                guid,
                entry.get("link"),
                entry.get("title"),
                entry.get("summary"),
                entry.get("comments"),
                _published(entry),
                fetched_at.isoformat(),
            ),
        )
        new += cursor.rowcount
    return len(feed.entries), new


def _published(entry: feedparser.FeedParserDict) -> str | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime(*parsed[:6], tzinfo=UTC).isoformat()
