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
    weights = {s.id: s.weight for s in sources}
    since = now - timedelta(hours=hours)

    by_story: dict[int, tuple[str, list[Item]]] = {}
    for row in conn.execute(
        """
        SELECT story.id AS story_id, story.lang, article.*, v.action, v.reason
        FROM story
        JOIN story_article ON story_article.story_id = story.id
        JOIN article ON article.id = story_article.article_id
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
            action=row["action"],
            reason=row["reason"],
        )
        by_story.setdefault(row["story_id"], (row["lang"], []))[1].append(item)

    stories = []
    dropped = []
    for story_id, (lang, items) in by_story.items():
        recent = [i for i in items if i.published >= since]
        dropped += [i for i in recent if i.action == "drop"]
        kept = [i for i in items if i.action != "drop"]
        if not any(i.published >= since for i in kept):
            continue
        stories.append(_score(story_id, lang, kept, weights, now))

    stories.sort(key=lambda s: (-s.score, -s.newest.timestamp(), s.id))
    dropped.sort(key=lambda i: (-i.published.timestamp(), i.id))
    return Ranking(tuple(stories), tuple(dropped))


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
