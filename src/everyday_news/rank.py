"""Rank stories for the digest: weight × recency × coverage × downrank.

Computed on demand from stories, articles and filter verdicts; nothing is stored.
"""

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta

from everyday_news.sources import Source

HALF_LIFE_HOURS = 24
EXTRA_SITE = 0.5
EXTRA_ARTICLE = 0.25
DOWNRANK = 0.5


@dataclass(frozen=True)
class Item:
    """One article as the digest sees it."""

    id: int
    source_id: str
    title: str
    url: str
    discussion_url: str | None
    text: str
    published: datetime
    fetched: datetime  # when this app first stored it
    action: str | None  # "drop", "downrank" or None
    reason: str | None


@dataclass(frozen=True)
class RankedStory:
    id: int
    lang: str
    lead: Item
    others: tuple[Item, ...]  # remaining kept articles, best first
    score: float
    weight: float
    recency: float
    coverage: float
    downranked: str | None  # reason, when every kept article is downranked

    @property
    def items(self) -> tuple[Item, ...]:
        return (self.lead, *self.others)

    @property
    def newest(self) -> datetime:
        return max(i.published for i in self.items)


@dataclass(frozen=True)
class Ranking:
    stories: tuple[RankedStory, ...]  # best first
    dropped: tuple[Item, ...]  # filtered-out articles in the window, newest first


def rank_stories(
    conn: sqlite3.Connection, sources: list[Source], now: datetime, hours: int
) -> Ranking:
    """Stories with a kept article inside its site's window (`digest_hours` of the source,
    else `hours`), best first, plus the dropped articles in the same windows."""
    weights = {s.id: s.weight for s in sources}
    windows = {s.id: timedelta(hours=s.digest_hours or hours) for s in sources}
    default_window = timedelta(hours=hours)

    def in_window(i: Item) -> bool:
        return i.published >= now - windows.get(i.source_id, default_window)

    by_story = _load_items(conn)
    stories = []
    dropped = []
    for story_id, (lang, items) in by_story.items():
        dropped += [i for i in items if i.action == "drop" and in_window(i)]
        kept = [i for i in items if i.action != "drop"]
        if not any(in_window(i) for i in kept):
            continue
        stories.append(_score(story_id, lang, kept, weights, now))

    stories.sort(key=lambda s: (-s.score, -s.newest.timestamp(), s.id))
    dropped.sort(key=lambda i: (-i.published.timestamp(), i.id))
    return Ranking(tuple(stories), tuple(dropped))


def stories_by_id(
    conn: sqlite3.Connection, sources: list[Source], now: datetime, ids: list[int]
) -> list[RankedStory]:
    """The given stories, scored but not limited by any window (for followed stories).
    Stories that no longer exist or have only dropped articles are skipped."""
    weights = {s.id: s.weight for s in sources}
    by_story = _load_items(conn)
    result = []
    for story_id in ids:
        lang, items = by_story.get(story_id, ("", []))
        kept = [i for i in items if i.action != "drop"]
        if kept:
            result.append(_score(story_id, lang, kept, weights, now))
    return result


def _load_items(conn: sqlite3.Connection) -> dict[int, tuple[str, list[Item]]]:
    """All story articles with their verdicts, grouped by story: {id: (lang, items)}."""
    by_story: dict[int, tuple[str, list[Item]]] = {}
    for row in conn.execute(
        """
        SELECT story.id AS story_id, story.lang, article.*, raw_item.fetched_at,
               v.action, v.reason
        FROM story
        JOIN story_article ON story_article.story_id = story.id
        JOIN article ON article.id = story_article.article_id
        JOIN raw_item ON raw_item.id = article.raw_item_id
        LEFT JOIN article_verdict v ON v.article_id = article.id
        """
    ):
        item = Item(
            id=row["id"],
            source_id=row["source_id"],
            title=row["title"],
            url=row["url"],
            discussion_url=row["discussion_url"],
            text=row["text"],
            published=datetime.fromisoformat(row["published_at"]),
            fetched=datetime.fromisoformat(row["fetched_at"]),
            action=row["action"],
            reason=row["reason"],
        )
        by_story.setdefault(row["story_id"], (row["lang"], []))[1].append(item)

    return by_story


def _score(
    story_id: int, lang: str, kept: list[Item], weights: dict[str, float], now: datetime
) -> RankedStory:
    def preference(i: Item) -> tuple:
        return (
            i.action == "downrank",
            -weights.get(i.source_id, 0.0),
            not i.text,
            i.published,
            i.id,
        )

    ordered = sorted(kept, key=preference)
    sites = {i.source_id for i in kept}
    weight = max(weights.get(i.source_id, 0.0) for i in kept)
    age_hours = max(0.0, (now - max(i.published for i in kept)).total_seconds() / 3600)
    recency = 0.5 ** (age_hours / HALF_LIFE_HOURS)
    coverage = 1 + EXTRA_SITE * (len(sites) - 1) + EXTRA_ARTICLE * (len(kept) - len(sites))
    downranked = ordered[0].reason if all(i.action == "downrank" for i in kept) else None
    score = weight * recency * coverage * (DOWNRANK if downranked else 1.0)
    return RankedStory(
        id=story_id,
        lang=lang,
        lead=ordered[0],
        others=tuple(ordered[1:]),
        score=score,
        weight=weight,
        recency=recency,
        coverage=coverage,
        downranked=downranked,
    )
