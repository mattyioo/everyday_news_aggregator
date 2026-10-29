"""Followed stories (stored in the DB by id) and followed topics (`follow.toml`)."""

import sqlite3
import tomllib
from datetime import datetime
from pathlib import Path

from everyday_news.keywords import is_single_word

DEFAULT_PATH = Path("follow.toml")


class FollowError(ValueError):
    """Raised for an unknown story id or an invalid `follow.toml`."""


def load_topics(path: Path = DEFAULT_PATH) -> tuple[str, ...]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FollowError(f"{path}: file not found") from None
    except tomllib.TOMLDecodeError as e:
        raise FollowError(f"{path}: invalid TOML: {e}") from None

    topics = data.get("topics", [])
    if not isinstance(topics, list) or not all(isinstance(t, str) for t in topics):
        raise FollowError(f"{path}: topics must be a list of strings")
    for t in topics:
        if not is_single_word(t):
            raise FollowError(f"{path}: topic {t!r} must be a single word")
    return tuple(dict.fromkeys(t.casefold() for t in topics))


def follow_story(conn: sqlite3.Connection, story_id: int, now: datetime) -> str:
    """Follow a story; returns its title. Following twice is harmless."""
    row = conn.execute("SELECT title FROM story WHERE id = ?", (story_id,)).fetchone()
    if row is None:
        raise FollowError(f"no story #{story_id} (ids are shown in the digest and `news top`)")
    conn.execute(
        "INSERT OR IGNORE INTO followed_story (story_id, followed_at) VALUES (?, ?)",
        (story_id, now.isoformat()),
    )
    conn.commit()
    return row["title"]


def unfollow_story(conn: sqlite3.Connection, story_id: int) -> bool:
    """Stop following; returns False when the story wasn't followed."""
    deleted = conn.execute("DELETE FROM followed_story WHERE story_id = ?", (story_id,))
    conn.commit()
    return deleted.rowcount > 0


def followed_ids(conn: sqlite3.Connection) -> list[int]:
    return [r[0] for r in conn.execute("SELECT story_id FROM followed_story ORDER BY followed_at")]
