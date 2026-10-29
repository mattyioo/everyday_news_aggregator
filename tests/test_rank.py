from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from everyday_news import db
from everyday_news.normalize import title_hash
from everyday_news.rank import rank_stories
from everyday_news.sources import Source

NOW = datetime(2026, 10, 29, 20, 0, tzinfo=UTC)
SOURCES = [
    Source(id="bbc", name="BBC", url="https://bbc.example/f", lang="en", weight=1.0),
    Source(id="hn", name="HN", url="https://hn.example/f", lang="en", weight=1.0),
    Source(id="wp", name="WP", url="https://wp.example/f", lang="pl", weight=0.5),
]


@pytest.fixture
def conn(tmp_path: Path):
    c = db.connect(tmp_path / "news.db")
    yield c
    c.close()


def story(conn, *articles: tuple, lang: str = "en") -> int:
    """Insert a story; each article is (source, hours_ago, title, text, verdict)."""
    story_id = conn.execute(
        "INSERT INTO story (lang, title, first_seen, last_updated) VALUES (?, 't', '', '')",
        (lang,),
    ).lastrowid
    for source, hours_ago, title, text, verdict in articles:
        n = conn.execute("SELECT COUNT(*) FROM article").fetchone()[0] + 1
        published = (NOW - timedelta(hours=hours_ago)).isoformat()
        raw_id = conn.execute(
            "INSERT INTO raw_item (source_id, guid, fetched_at) VALUES (?, ?, ?)",
            (source, f"g{n}", published),
        ).lastrowid
        article_id = conn.execute(
            "INSERT INTO article (raw_item_id, source_id, lang, url, title, text, published_at,"
            " title_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (raw_id, source, lang, f"https://x/{n}", title, text, published, title_hash(title)),
        ).lastrowid
        conn.execute("INSERT INTO story_article VALUES (?, ?)", (story_id, article_id))
        if verdict:
            action, reason = verdict
            conn.execute(
                "INSERT INTO article_verdict VALUES (?, ?, ?)", (article_id, action, reason)
            )
    return story_id


def rank(conn, hours: int = 24):
    return rank_stories(conn, SOURCES, NOW, hours)


def test_score_parts(conn) -> None:
    story(
        conn, ("bbc", 24, "A", "text", None), ("hn", 24, "B", "", None), ("bbc", 30, "C", "x", None)
    )
    (s,) = rank(conn).stories
    assert s.weight == 1.0
    assert s.recency == pytest.approx(0.5)  # newest article is one half-life old
    assert s.coverage == pytest.approx(1 + 0.5 + 0.25)  # 2 sites, 1 extra same-site article
    assert s.score == pytest.approx(0.875)


def test_coverage_beats_single_article_of_same_age(conn) -> None:
    single = story(conn, ("bbc", 2, "Single", "t", None))
    multi = story(conn, ("bbc", 2, "Multi", "t", None), ("hn", 3, "Multi too", "", None))
    assert [s.id for s in rank(conn).stories] == [multi, single]


def test_lead_prefers_normal_then_weight_then_text_then_earliest(conn) -> None:
    story(
        conn,
        ("bbc", 1, "Watch: video", "t", ("downrank", "video")),
        ("hn", 3, "HN no text", "", None),
        ("bbc", 2, "BBC later", "text", None),
        ("bbc", 4, "BBC earlier", "text", None),
    )
    (s,) = rank(conn).stories
    assert s.lead.title == "BBC earlier"
    assert [i.title for i in s.others] == ["BBC later", "HN no text", "Watch: video"]
    assert s.downranked is None


def test_fully_downranked_story_scores_half(conn) -> None:
    story(conn, ("bbc", 0, "Watch: a", "t", ("downrank", "video")))
    story(conn, ("hn", 0, "Plain", "t", None))
    plain, video = rank(conn).stories
    assert (plain.lead.title, video.lead.title) == ("Plain", "Watch: a")
    assert video.downranked == "video"
    assert video.score == pytest.approx(plain.score / 2)


def test_dropped_articles_are_hidden_and_listed(conn) -> None:
    story(conn, ("wp", 1, "Aż 1,5 mln wyświetleń", "t", ("drop", "bait")),
          ("wp", 2, "Budują estakadę", "t", None), lang="pl")  # fmt: skip
    story(conn, ("wp", 1, "Szok!", "t", ("drop", "bait")), lang="pl")
    ranking = rank(conn)
    assert [s.lead.title for s in ranking.stories] == ["Budują estakadę"]
    assert ranking.stories[0].others == ()
    assert [i.title for i in ranking.dropped] == ["Aż 1,5 mln wyświetleń", "Szok!"]


def test_window_uses_newest_kept_article(conn) -> None:
    story(conn, ("bbc", 30, "Old", "t", None))
    story(conn, ("bbc", 30, "Old but updated", "t", None), ("hn", 5, "Update", "", None))
    story(conn, ("bbc", 30, "Old", "t", None), ("hn", 5, "Dropped update", "", ("drop", "x")))
    titles = [s.lead.title for s in rank(conn).stories]
    assert titles == ["Old but updated"]
    assert [s.lead.title for s in rank(conn, hours=48).stories] == [
        "Old but updated", "Old", "Old",
    ]  # fmt: skip


def test_per_site_window_overrides_global(tmp_path: Path) -> None:
    conn = db.connect(tmp_path / "w.db")
    slow = Source(id="zn", name="ZN", url="https://zn.example/f", lang="pl", digest_hours=168)
    story(conn, ("zn", 100, "Slow site post", "t", None), lang="pl")
    story(conn, ("bbc", 100, "Old BBC", "t", None))
    story(conn, ("zn", 200, "Too old even for 7 days", "t", None), lang="pl")
    ranking = rank_stories(conn, [*SOURCES, slow], NOW, 24)
    assert [s.lead.title for s in ranking.stories] == ["Slow site post"]
    conn.close()


def test_primary_borrows_discussion_link_from_its_duplicate(conn) -> None:
    story(conn, ("bbc", 1, "Spain crash: what we know", "Lead.", None))
    raw = conn.execute(
        "INSERT INTO raw_item (source_id, guid, fetched_at) VALUES ('hn', 'dup', ?)",
        (NOW.isoformat(),),
    ).lastrowid
    conn.execute(
        "INSERT INTO article (raw_item_id, source_id, lang, url, discussion_url, title, text,"
        " published_at, title_hash, duplicate_of) VALUES (?, 'hn', 'en', 'https://x/1',"
        " 'https://news.ycombinator.com/item?id=1', 'Spain crash', '', ?, 'h', 1)",
        (raw, NOW.isoformat()),
    )
    (s,) = rank(conn).stories
    assert s.lead.discussion_url == "https://news.ycombinator.com/item?id=1"
