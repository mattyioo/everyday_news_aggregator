"""Group articles about the same event into stories, per language.

Incremental: an article is assigned once and keeps its story, so story ids stay
stable. A new article joins the most similar story whose newest article is
within WINDOW; otherwise it starts a new story.

Similarity uses "key words": words of 3+ characters, stopwords removed, cut to
a 5-character prefix so inflected forms match (iPhona/iPhone -> "iphon").
"""

import re
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from everyday_news.sources import Source

WINDOW = timedelta(days=3)
FOLLOWED_WINDOW = timedelta(days=30)  # followed stories may go quiet for a while
STEM = 5
TITLE_MIN = 0.3  # Jaccard of title key words, or...
SHARED_MIN = 2  # ...this many shared title key words (names, places)...
SHARED_TITLE_MIN = 0.15  # ...with at least this Jaccard (long headlines dilute it)
TEXT_MIN = 0.4  # overlap of title+text key words...
TEXT_MIN_WORDS = 8  # ...only when both sides have this many (HN items have no text)

STOPWORDS = {
    # English
    "the", "and", "for", "are", "was", "were", "but", "not", "you", "your", "with", "from",
    "this", "that", "these", "those", "have", "has", "had", "will", "would", "can", "could",
    "about", "after", "before", "into", "over", "under", "than", "then", "they", "their",
    "them", "what", "when", "where", "which", "who", "why", "how", "all", "any", "more",
    "most", "some", "such", "its", "his", "her", "our", "out", "off", "new", "now", "just",
    "says", "said", "say", "here", "there", "been", "being", "also", "know", "far", "watch",
    "video", "live", "first", "one", "two", "three", "four", "per", "via", "least", "show",
    # Polish
    "się", "nie", "jak", "już", "tak", "ale", "czy", "dla", "pod", "nad", "ich", "jej",
    "jego", "ten", "tym", "tej", "tego", "temu", "też", "oraz", "przez", "jako", "tylko",
    "jednak", "który", "która", "które", "którzy", "będzie", "może", "mogą", "został",
    "została", "zostało", "także", "również", "aby", "żeby", "kiedy", "gdzie", "teraz",
    "dziś", "jeszcze", "bardzo", "więcej", "nowy", "nowa", "nowe", "nowego", "pierwszy",
    "jest", "był", "była", "było", "być", "mają", "przy", "bez", "przed", "tam", "wraz",
}  # fmt: skip

WORD = re.compile(r"\w+")


def key_words(text: str) -> set[str]:
    return {
        w[:STEM]
        for w in WORD.findall(text.casefold())
        if len(w) >= 3 and w not in STOPWORDS and not w.isdigit()
    }


@dataclass
class _Article:
    id: int
    title_keys: set[str]
    all_keys: set[str]
    published: datetime


@dataclass
class _Story:
    id: int
    lang: str
    members: list[_Article] = field(default_factory=list)

    @property
    def newest(self) -> datetime:
        return max(a.published for a in self.members)


def similarity(a: _Article, b: _Article) -> float:
    """Best of the title and (when both have enough words) text measures,
    each scaled so 1.0 means "at its threshold"."""
    shared = a.title_keys & b.title_keys
    union = a.title_keys | b.title_keys
    title = len(shared) / len(union) if union else 0.0
    score = title / TITLE_MIN
    if len(shared) >= SHARED_MIN and title >= SHARED_TITLE_MIN:
        score = max(score, 1.0)
    if len(a.all_keys) >= TEXT_MIN_WORDS and len(b.all_keys) >= TEXT_MIN_WORDS:
        overlap = len(a.all_keys & b.all_keys) / min(len(a.all_keys), len(b.all_keys))
        score = max(score, overlap / TEXT_MIN)
    return score


def _load(row: sqlite3.Row) -> _Article:
    return _Article(
        id=row["id"],
        title_keys=key_words(row["title"]),
        all_keys=key_words(f"{row['title']} {row['text']}"),
        published=datetime.fromisoformat(row["published_at"]),
    )


def cluster(conn: sqlite3.Connection, sources: list[Source]) -> int:
    """Assign unassigned primary articles to stories. Returns how many were assigned."""
    # Articles that became duplicates (or were deleted) leave their story; empty stories go.
    conn.execute(
        """
        DELETE FROM story_article WHERE article_id NOT IN
            (SELECT id FROM article WHERE duplicate_of IS NULL)
        """
    )
    conn.execute("DELETE FROM story WHERE id NOT IN (SELECT story_id FROM story_article)")
    conn.execute("DELETE FROM followed_story WHERE story_id NOT IN (SELECT id FROM story)")
    followed = {r[0] for r in conn.execute("SELECT story_id FROM followed_story")}

    articles = {
        row["id"]: (row, _load(row))
        for row in conn.execute(
            "SELECT * FROM article WHERE duplicate_of IS NULL ORDER BY published_at, id"
        )
    }
    stories: dict[int, _Story] = {}
    for link in conn.execute(
        "SELECT story_id, article_id, lang FROM story_article"
        " JOIN story ON story.id = story_article.story_id"
    ):
        story = stories.setdefault(link["story_id"], _Story(link["story_id"], link["lang"]))
        story.members.append(articles[link["article_id"]][1])

    assigned_ids = {a.id for s in stories.values() for a in s.members}
    assigned = 0
    for row, article in articles.values():
        if article.id in assigned_ids:
            continue
        candidates = [
            (max(similarity(article, m) for m in s.members), s)
            for s in stories.values()
            if s.lang == row["lang"]
            and abs(article.published - s.newest)
            <= (FOLLOWED_WINDOW if s.id in followed else WINDOW)
        ]
        score, best = max(candidates, key=lambda c: c[0], default=(0.0, None))
        if best is None or score < 1.0:
            story_id = conn.execute(
                "INSERT INTO story (lang, title, first_seen, last_updated) VALUES (?, ?, ?, ?)",
                (row["lang"], row["title"], row["published_at"], row["published_at"]),
            ).lastrowid
            best = stories[story_id] = _Story(story_id, row["lang"])
        conn.execute(
            "INSERT INTO story_article (story_id, article_id) VALUES (?, ?)",
            (best.id, article.id),
        )
        best.members.append(article)
        assigned += 1

    _refresh_story_fields(conn, sources)
    conn.commit()
    return assigned


def _refresh_story_fields(conn: sqlite3.Connection, sources: list[Source]) -> None:
    """Title from the highest-weight source (earliest on ties); first/last dates."""
    weights = {s.id: s.weight for s in sources}
    rows = conn.execute(
        """
        SELECT story_article.story_id, article.source_id, article.title, article.published_at
        FROM story_article JOIN article ON article.id = story_article.article_id
        ORDER BY article.published_at, article.id
        """
    ).fetchall()
    by_story: dict[int, list[sqlite3.Row]] = {}
    for r in rows:
        by_story.setdefault(r["story_id"], []).append(r)
    for story_id, members in by_story.items():
        lead = min(members, key=lambda r: -weights.get(r["source_id"], 0.0))
        conn.execute(
            "UPDATE story SET title = ?, first_seen = ?, last_updated = ? WHERE id = ?",
            (lead["title"], members[0]["published_at"], members[-1]["published_at"], story_id),
        )
