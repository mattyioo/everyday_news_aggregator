import re
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from everyday_news import db
from everyday_news.fetch import fetch_all, make_client
from everyday_news.normalize import canonical_url, normalize_pending, parse_html, title_hash
from everyday_news.sources import Source

FIXTURES = Path(__file__).parent / "fixtures"
# Reddit is no longer configured, but its fixture keeps the generic `[link]` rule covered.
LANGS = {"hn": "en", "bbc": "en", "reddit-technology": "en", "wp": "pl", "znosnenewsy": "pl"}
SOURCES = [
    Source(id=i, name=i, url=f"https://{i}.example/feed", lang=lang) for i, lang in LANGS.items()
]


@pytest.fixture
def conn(tmp_path: Path):
    """A database filled from the four real feed fixtures."""
    c = db.connect(tmp_path / "news.db")

    def serve(request: httpx.Request) -> httpx.Response:
        name = request.url.host.removesuffix(".example")
        return httpx.Response(200, content=(FIXTURES / f"{name}.xml").read_bytes())

    with make_client(httpx.MockTransport(serve)) as client:
        fetch_all(
            SOURCES,
            c,
            client,
            now=lambda: datetime(2026, 10, 29, tzinfo=UTC),
            sleep=lambda seconds: None,
        )
    yield c
    c.close()


def articles(conn, source_id: str) -> list:
    return conn.execute(
        "SELECT * FROM article WHERE source_id = ? ORDER BY id", (source_id,)
    ).fetchall()


def test_every_raw_item_becomes_one_clean_article(conn) -> None:
    assert normalize_pending(conn, SOURCES) == 15
    for row in conn.execute("SELECT * FROM article"):
        assert row["title"] and row["url"].startswith("https://")
        assert row["lang"] == LANGS[row["source_id"]]
        for field in ("title", "text"):
            assert not re.search(r"<[a-z/]|&[#a-z0-9]+;", row[field]), row[field]
        assert datetime.fromisoformat(row["published_at"]).tzinfo is not None


def test_normalize_is_idempotent(conn) -> None:
    normalize_pending(conn, SOURCES)
    assert normalize_pending(conn, SOURCES) == 0
    assert conn.execute("SELECT COUNT(*) FROM article").fetchone()[0] == 15


def test_hacker_news_keeps_discussion_and_drops_comments_text(conn) -> None:
    normalize_pending(conn, SOURCES)
    first = articles(conn, "hn")[0]
    assert first["url"] == "https://mistral.ai/news/mistral-large-4-oss/"
    assert first["discussion_url"] == "https://news.ycombinator.com/item?id=50289418"
    assert first["text"] == ""


def test_reddit_points_at_external_article(conn) -> None:
    normalize_pending(conn, SOURCES)
    first = articles(conn, "reddit-technology")[0]
    assert first["url"].startswith("https://www.tomshardware.com/")
    assert first["discussion_url"].startswith("https://www.reddit.com/r/technology/comments/")
    assert "submitted by" not in first["text"]


def test_wordpress_footer_and_ellipsis_removed(conn) -> None:
    normalize_pending(conn, SOURCES)
    first = articles(conn, "znosnenewsy")[0]
    assert first["text"].startswith("Apple wypuściło")
    assert first["text"].endswith("obsługą dotykową.")
    assert "pochodzi z serwisu" not in first["text"]


def test_bbc_tracking_params_removed(conn) -> None:
    normalize_pending(conn, SOURCES)
    for row in articles(conn, "bbc"):
        assert row["url"].startswith("https://www.bbc.co.uk/news/articles/")
        assert "?" not in row["url"]
        assert row["text"]


def test_wp_image_dropped_lead_kept(conn) -> None:
    normalize_pending(conn, SOURCES)
    first = articles(conn, "wp")[0]
    assert first["text"].startswith("Prezydent USA Donald Trump")
    assert first["discussion_url"] is None


def test_unknown_source_is_left_pending(conn) -> None:
    only_hn = [s for s in SOURCES if s.id == "hn"]
    assert normalize_pending(conn, only_hn) == 3
    assert normalize_pending(conn, SOURCES) == 12


def test_canonical_url_strips_tracking_only() -> None:
    url = "HTTPS://Example.COM/a/b?id=7&utm_source=x&utm_medium=y&fbclid=z#frag"
    assert canonical_url(url) == "https://example.com/a/b?id=7#frag"
    bbc = "https://www.bbc.co.uk/news/articles/c1?at_medium=RSS&at_campaign=rss"
    assert canonical_url(bbc) == "https://www.bbc.co.uk/news/articles/c1"


def test_title_hash_ignores_case_punctuation_and_spacing() -> None:
    assert title_hash("Trump o wyborach:  „Wstyd”!") == title_hash("trump o WYBORACH wstyd")
    assert title_hash("Apple") != title_hash("Apples")


def test_parse_html_collects_text_and_links() -> None:
    text, links = parse_html('<p>Hi <a href="https://x">there</a></p><img src="y">')
    assert text.strip() == "Hi there"
    assert links == [("https://x", "there")]
