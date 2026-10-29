from pathlib import Path

import pytest

from everyday_news.webview import digest_dates, render_markdown, route

DIGEST = """# Everyday News – 2026-10-29

_Generated 20:00 · last 24 h · 2 stories from 1 sites · 0 filtered out_

## BBC News World (2)

- 🆕 **[Spain train crash](https://www.bbc.co.uk/news/1)**
  More than 500 passengers.
  _11:00 · [discussion](https://news.ycombinator.com/item?id=1) · \\#15_
"""


@pytest.fixture
def digests(tmp_path: Path) -> Path:
    d = tmp_path / "digests"
    d.mkdir()
    (d / "2026-10-28.md").write_text("# Everyday News – 2026-10-28\n", encoding="utf-8")
    (d / "2026-10-29.md").write_text(DIGEST, encoding="utf-8")
    (d / "notes.md").write_text("# not a digest\n", encoding="utf-8")
    return d


def test_latest_digest_at_root(digests: Path) -> None:
    r = route("/", digests)
    assert r.status == 200 and r.content_type.startswith("text/html")
    assert "<h1>Everyday News – 2026-10-29</h1>" in r.body
    assert "<h2>BBC News World (2)</h2>" in r.body
    assert (
        '<a href="https://www.bbc.co.uk/news/1" target="_blank" rel="noopener noreferrer">'
        in r.body
    )
    assert "#15" in r.body and "\\#15" not in r.body
    assert '<a href="/d/2026-10-28">← 2026-10-28</a>' in r.body


def test_specific_day_and_navigation(digests: Path) -> None:
    r = route("/d/2026-10-28", digests)
    assert r.status == 200 and "2026-10-28" in r.body
    assert '<a href="/d/2026-10-29">2026-10-29 →</a>' in r.body


def test_archive_lists_only_digest_files(digests: Path) -> None:
    assert digest_dates(digests) == ["2026-10-29", "2026-10-28"]
    body = route("/archive", digests).body
    assert body.count('<a href="/d/') == 2 and "notes" not in body


@pytest.mark.parametrize(
    "path",
    ["/d/2026-10-30", "/d/../../etc/passwd", "/d/notes", "/digests/2026-10-29.md", "/x"],
)
def test_unknown_paths_are_404(digests: Path, path: str) -> None:
    r = route(path, digests)
    assert r.status == 404


def test_404_does_not_reflect_markup(digests: Path) -> None:
    body = route("/<script>alert(1)</script>", digests).body
    assert "<script>" not in body and "&lt;script&gt;" in body


def test_no_digests_yet(tmp_path: Path) -> None:
    r = route("/", tmp_path / "missing")
    assert r.status == 200 and "No digest yet" in r.body


def test_raw_html_and_unsafe_links_are_not_rendered() -> None:
    out = render_markdown('<img src=x onerror="alert(1)"> [x](javascript:alert(1))')
    assert "<img" not in out
    assert 'href="javascript:' not in out
