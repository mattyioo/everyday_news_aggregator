"""Turn raw feed items into clean `Article`s: plain text, canonical URLs, UTC dates.

Rules key off the shape of the feed (a Reddit-style `[link]`, an HN comments
URL, a WordPress footer), not off source ids, so new sources of the same kind
work without code changes.
"""

import hashlib
import re
import sqlite3
import unicodedata
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from everyday_news.sources import Source

TRACKING_PARAMS = {"fbclid", "gclid", "mc_cid", "mc_eid", "ref_src", "at_medium", "at_campaign"}

# WordPress footers: "Artykuł X pochodzi z serwisu Y." / "The post X appeared first on Y."
FOOTERS = [
    re.compile(r"Artykuł .+? pochodzi z serwisu .+?\.?$", re.S),
    re.compile(r"The post .+? appeared first on .+?\.?$", re.S),
]
ELLIPSIS = re.compile(r"\s*\[(?:…|\.\.\.)\]\s*")


@dataclass(frozen=True)
class Article:
    source_id: str
    lang: str
    url: str
    discussion_url: str | None
    title: str
    text: str
    published_at: str
    title_hash: str


class _TextExtractor(HTMLParser):
    """Collect visible text and link targets; images are dropped."""

    BLOCKS = {"p", "br", "div", "li", "tr", "td", "h1", "h2", "h3", "h4", "blockquote"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.links: list[tuple[str, str]] = []  # (href, text)
        self._href: str | None = None
        self._link_text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.BLOCKS:
            self.parts.append("\n")
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._link_text = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href is not None:
            self.links.append((self._href, "".join(self._link_text).strip()))
            self._href = None
        if tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        self.parts.append(data)
        if self._href is not None:
            self._link_text.append(data)


def parse_html(html: str) -> tuple[str, list[tuple[str, str]]]:
    """Return (plain text, links) for an HTML fragment."""
    extractor = _TextExtractor()
    extractor.feed(html)
    extractor.close()
    return "".join(extractor.parts), extractor.links


def collapse(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def canonical_url(url: str) -> str:
    """Lowercase scheme/host and drop tracking query params."""
    parts = urlsplit(url.strip())
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not k.startswith("utm_") and k not in TRACKING_PARAMS
    ]
    return urlunsplit(
        (parts.scheme.lower(), parts.netloc.lower(), parts.path, urlencode(query), parts.fragment)
    )


def title_hash(title: str) -> str:
    """Hash of the title with case, punctuation and spacing ignored."""
    folded = unicodedata.normalize("NFKC", title).casefold()
    words = re.sub(r"[^\w\s]", " ", folded)
    return hashlib.sha256(collapse(words).encode()).hexdigest()


def _reddit_parts(summary: str) -> tuple[str | None, str] | None:
    """For a Reddit-style summary return (external url, self-text), else None."""
    _, links = parse_html(summary)
    link = next((href for href, text in links if text == "[link]"), None)
    if link is None:
        return None
    # Self-text, if any, sits in <div class="md">; the rest is "submitted by" boilerplate.
    match = re.search(r'<div class="md">(.*?)</div>', summary, re.S)
    body = collapse(parse_html(match.group(1))[0]) if match else ""
    return link, body


def _clean_text(summary: str) -> str:
    text, _ = parse_html(summary)
    text = collapse(text)
    for footer in FOOTERS:
        text = footer.sub("", text).strip()
    text = ELLIPSIS.sub(" ", text).strip()
    return "" if text == "Comments" else text


def normalize_item(row: sqlite3.Row, source: Source) -> Article | None:
    """Build an Article from a raw_item row, or None if it has no usable title/url."""
    title = collapse(parse_html(row["title"] or "")[0])
    url = row["url"]
    discussion_url = row["comments_url"]
    summary = row["summary"] or ""

    reddit = _reddit_parts(summary)
    if reddit:
        external, text = reddit
        if external and external != url:
            discussion_url, url = url, external
    else:
        text = _clean_text(summary)

    if discussion_url == url:
        discussion_url = None  # e.g. "Ask HN": the item is the discussion
    if not title or not url or not url.startswith(("http://", "https://")):
        return None

    return Article(
        source_id=source.id,
        lang=source.lang,
        url=canonical_url(url),
        discussion_url=discussion_url,
        title=title,
        text=text,
        published_at=row["published"] or row["fetched_at"],
        title_hash=title_hash(title),
    )


def normalize_pending(conn: sqlite3.Connection, sources: list[Source]) -> int:
    """Normalize raw items that have no article yet. Returns how many were added.

    Items whose source is no longer configured are left for later.
    """
    by_id = {s.id: s for s in sources}
    rows = conn.execute(
        """
        SELECT raw_item.* FROM raw_item
        LEFT JOIN article ON article.raw_item_id = raw_item.id
        WHERE article.id IS NULL
        ORDER BY raw_item.id
        """
    ).fetchall()

    added = 0
    for row in rows:
        source = by_id.get(row["source_id"])
        article = normalize_item(row, source) if source else None
        if article is None:
            continue
        conn.execute(
            """
            INSERT INTO article (raw_item_id, source_id, lang, url, discussion_url,
                                 title, text, published_at, title_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                article.source_id,
                article.lang,
                article.url,
                article.discussion_url,
                article.title,
                article.text,
                article.published_at,
                article.title_hash,
            ),
        )
        added += 1
    conn.commit()
    return added
