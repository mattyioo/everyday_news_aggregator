"""Delete old news: raw items (and their articles) not seen in their feed for N days.

"Last seen" rather than publish date: an item that is still in a feed must not be
deleted, or the next fetch would import it again as new.
"""

import sqlite3
from datetime import datetime, timedelta

from everyday_news.sources import Source


def prune(
    conn: sqlite3.Connection, sources: list[Source], retention_days: int, now: datetime
) -> int:
    """Delete everything unseen for `retention_days`, except articles of followed
    stories. Returns how many articles went."""
    cutoff = (now - timedelta(days=retention_days)).isoformat()
    stale = """
        SELECT id FROM raw_item WHERE last_seen_at < ? AND id NOT IN (
            SELECT article.raw_item_id FROM article
            JOIN story_article ON story_article.article_id = article.id
            JOIN followed_story ON followed_story.story_id = story_article.story_id
        )
    """

    deleted = conn.execute(f"DELETE FROM article WHERE raw_item_id IN ({stale})", (cutoff,))
    conn.execute(f"DELETE FROM raw_item WHERE id IN ({stale})", (cutoff,))

    # Fetch state of sources removed from sources.toml is never read again
    ids = [s.id for s in sources]
    placeholders = ",".join("?" * len(ids))
    conn.execute(f"DELETE FROM fetch_state WHERE source_id NOT IN ({placeholders})", ids)

    conn.commit()
    return deleted.rowcount
