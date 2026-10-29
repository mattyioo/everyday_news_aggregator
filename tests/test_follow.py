from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from everyday_news import db
from everyday_news.cli import app
from everyday_news.cluster import cluster
from everyday_news.digest import Following, render_digest
from everyday_news.follow import (
    FollowError,
    follow_story,
    followed_ids,
    load_topics,
    unfollow_story,
)
from everyday_news.keywords import find_keyword
from everyday_news.normalize import title_hash
from everyday_news.prune import prune
from everyday_news.rank import Item, RankedStory, Ranking
from everyday_news.settings import Settings
from everyday_news.sources import Source

NOW = datetime(2026, 10, 29, 19, 0, tzinfo=UTC)
SINCE = NOW - timedelta(hours=3)
WARSAW = timezone(timedelta(hours=1))
BBC = Source(id="bbc", name="BBC News World", url="https://bbc.example/f", lang="en")
SETTINGS = Settings(retention_days=7, digest_hours=24, stories_per_site=10)


@pytest.fixture
def conn(tmp_path: Path):
    c = db.connect(tmp_path / "news.db")
    yield c
    c.close()


def add_article(conn, title: str, published: datetime, last_seen: datetime | None = None) -> int:
    n = conn.execute("SELECT COUNT(*) FROM raw_item").fetchone()[0] + 1
    seen = (last_seen or published).isoformat()
    raw = conn.execute(
        "INSERT INTO raw_item (source_id, guid, fetched_at, last_seen_at) VALUES ('bbc', ?, ?, ?)",
        (f"g{n}", published.isoformat(), seen),
    ).lastrowid
    return conn.execute(
        "INSERT INTO article (raw_item_id, source_id, lang, url, title, text, published_at,"
        " title_hash) VALUES (?, 'bbc', 'en', ?, ?, '', ?, ?)",
        (raw, f"https://x/{n}", title, published.isoformat(), title_hash(title)),
    ).lastrowid


# --- storage -------------------------------------------------------------------


def test_follow_unfollow_and_unknown_story(conn) -> None:
    add_article(conn, "Spain train crash investigation", NOW)
    cluster(conn, [BBC])
    (story_id,) = [r[0] for r in conn.execute("SELECT id FROM story")]

    assert follow_story(conn, story_id, NOW) == "Spain train crash investigation"
    follow_story(conn, story_id, NOW)  # twice is fine
    assert followed_ids(conn) == [story_id]
    assert unfollow_story(conn, story_id) is True
    assert unfollow_story(conn, story_id) is False
    with pytest.raises(FollowError, match="no story #999"):
        follow_story(conn, 999, NOW)


def test_topics_file(tmp_path: Path) -> None:
    path = tmp_path / "follow.toml"
    path.write_text('topics = ["Ukrain", "ukrain", "f1"]\n', encoding="utf-8")
    assert load_topics(path) == ("ukrain", "f1")
    path.write_text('topics = ["two words"]\n', encoding="utf-8")
    with pytest.raises(FollowError, match="single word"):
        load_topics(path)
    assert load_topics(Path(__file__).parent.parent / "follow.toml") == ()


def test_find_keyword_stems_and_short_words() -> None:
    assert find_keyword("Atak na Ukrainę", ("ukrain",)) == "ukrain"
    assert find_keyword("F1 race", ("f1",)) == "f1"
    assert find_keyword("F150 recall", ("f1",)) is None


# --- clustering and retention ------------------------------------------------


def test_followed_story_keeps_growing_after_a_quiet_week(conn) -> None:
    add_article(conn, "Spain train crash investigation", NOW - timedelta(days=10))
    cluster(conn, [BBC])
    (story_id,) = [r[0] for r in conn.execute("SELECT id FROM story")]
    follow_story(conn, story_id, NOW)

    add_article(conn, "Spain train crash investigation report", NOW)
    cluster(conn, [BBC])
    assert conn.execute("SELECT COUNT(*) FROM story").fetchone()[0] == 1

    unfollow_story(conn, story_id)
    add_article(conn, "Spain train crash investigation ends", NOW + timedelta(days=10))
    cluster(conn, [BBC])
    assert conn.execute("SELECT COUNT(*) FROM story").fetchone()[0] == 2


def test_followed_story_articles_survive_retention(conn) -> None:
    old = NOW - timedelta(days=20)
    add_article(conn, "Followed story", old)
    add_article(conn, "Unrelated old piece about gardening", old)
    cluster(conn, [BBC])
    followed = conn.execute("SELECT id FROM story WHERE title = 'Followed story'").fetchone()[0]
    follow_story(conn, followed, NOW)

    assert prune(conn, [BBC], 7, NOW) == 1
    titles = [r[0] for r in conn.execute("SELECT title FROM article")]
    assert titles == ["Followed story"]


def test_follow_of_deleted_story_is_cleaned_up(conn) -> None:
    article = add_article(conn, "Gone soon", NOW)
    cluster(conn, [BBC])
    story_id = conn.execute("SELECT id FROM story").fetchone()[0]
    follow_story(conn, story_id, NOW)
    conn.execute("DELETE FROM article WHERE id = ?", (article,))
    cluster(conn, [BBC])
    assert followed_ids(conn) == []


# --- digest -----------------------------------------------------------------


def item(n: int, title: str, hours_ago: float, text: str = "", fetched_hours_ago=None) -> Item:
    published = NOW - timedelta(hours=hours_ago)
    fetched = NOW - timedelta(
        hours=fetched_hours_ago if fetched_hours_ago is not None else hours_ago
    )
    return Item(n, "bbc", title, f"https://x/{n}", None, text, published, fetched, None, None)


def story(n: int, *items: Item) -> RankedStory:
    return RankedStory(n, "en", items[0], items[1:], 1.0, 1.0, 1.0, 1.0, None)


def render(ranking: Ranking, following: Following, since=SINCE) -> str:
    return render_digest(ranking, [BBC], SETTINGS, NOW, WARSAW, since, following)


def test_followed_story_shows_only_its_updates() -> None:
    old = item(1, "Spain train crash: what we know", 48, "Old summary.")
    update = item(2, "Spain crash: drivers questioned", 1)
    followed = story(7, old, update)
    md = render(Ranking((followed,), ()), Following(stories=(followed,)))

    section = md[md.index("## Following") : md.index("## BBC News World")]
    assert "- 📌 **[Spain train crash: what we know](https://x/1)** · \\#7" in section
    assert "  - [Spain crash: drivers questioned](https://x/2) · BBC News World · 19:00" in section
    assert "Old summary." not in section  # only the update, not the old article
    assert "drivers questioned" not in md[md.index("## BBC News World") :]  # no repeat


def test_followed_story_without_updates_and_first_digest() -> None:
    quiet = story(8, item(1, "Quiet story", 30))
    md = render(Ranking((), ()), Following(stories=(quiet,)))
    assert "- 📌 **[Quiet story](https://x/1)** · \\#8\n  _no updates since your last digest_" in md
    first = render(Ranking((), ()), Following(stories=(quiet,)), since=None)
    assert "_first digest: updates will show from the next one_" in first


def test_topic_matches_are_listed_once_under_following() -> None:
    match = story(1, item(1, "Russian drone attack on Ukrainian station", 1))
    seen_match = story(2, item(2, "Ukraine peace talks", 10))  # before SINCE: not new
    other = story(3, item(3, "Bahamas carnival", 1))
    md = render(Ranking((match, seen_match, other), ()), Following(topics=("ukrain",)))

    following, sections = md.split("## BBC News World")
    assert "**Topic: ukrain** (1)" in following
    assert "Russian drone attack" in following and "Russian drone attack" not in sections
    assert "Ukraine peace talks" in sections  # seen before: stays in its site section
    assert "Bahamas carnival" in sections


def test_no_following_section_when_nothing_is_followed() -> None:
    md = render(Ranking((story(1, item(1, "Anything", 1)),), ()), Following())
    assert "## Following" not in md


# --- CLI ----------------------------------------------------------------------


def test_cli_follow_commands(tmp_path: Path) -> None:
    db_path = tmp_path / "news.db"
    conn = db.connect(db_path)
    add_article(conn, "Spain train crash investigation", NOW)
    cluster(conn, [BBC])
    story_id = conn.execute("SELECT id FROM story").fetchone()[0]
    conn.close()

    runner = CliRunner()
    cfg = ["--config", str(Path(__file__).parent.parent / "sources.toml"), "--db", str(db_path)]
    ok = runner.invoke(app, ["follow", str(story_id), *cfg])
    assert ok.exit_code == 0 and f"following #{story_id}" in ok.output
    listed = runner.invoke(app, ["following", *cfg])
    assert f"#{story_id}" in listed.output and "Spain train crash" in listed.output
    bad = runner.invoke(app, ["follow", "999", *cfg])
    assert bad.exit_code == 1 and "no story #999" in bad.output
    gone = runner.invoke(app, ["unfollow", str(story_id), "--db", str(db_path)])
    assert f"unfollowed #{story_id}" in gone.output
