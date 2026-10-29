from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

from everyday_news.digest import digest_path, escape, render_digest, write_digest
from everyday_news.rank import Item, RankedStory, Ranking
from everyday_news.settings import Settings
from everyday_news.sources import Source

WARSAW = timezone(timedelta(hours=1))  # CET, as on 2026-10-29
NOW = datetime(2026, 10, 29, 19, 0, tzinfo=UTC)
SOURCES = [
    Source(id="hn", name="Hacker News", url="https://hn.example/f", lang="en"),
    Source(id="bbc", name="BBC News World", url="https://bbc.example/f", lang="en"),
    Source(id="wp", name="WP.pl Wiadomości", url="https://wp.example/f", lang="pl"),
    Source(id="off", name="Disabled", url="https://off.example/f", lang="en", enabled=False),
]
SETTINGS = Settings(retention_days=7, digest_hours=24, stories_per_site=2)


def item(n: int, source: str, title: str, text: str = "", hours_ago: float = 1, **kw) -> Item:
    return Item(
        id=n,
        source_id=source,
        title=title,
        url=f"https://x/{n}",
        discussion_url=kw.get("discussion"),
        text=text,
        published=NOW - timedelta(hours=hours_ago),
        action=kw.get("action"),
        reason=kw.get("reason"),
    )


def story(n: int, lead: Item, *others: Item, score: float = 1.0, downranked=None) -> RankedStory:
    return RankedStory(n, "en", lead, others, score, 1.0, 1.0, 1.0, downranked)


def render(*stories: RankedStory, dropped: tuple[Item, ...] = ()) -> str:
    return render_digest(Ranking(stories, dropped), SOURCES, SETTINGS, NOW, tz=WARSAW)


def test_header_and_one_section_per_enabled_site_in_config_order() -> None:
    md = render(story(1, item(1, "bbc", "Spain train crash", "Many passengers.")))
    lines = md.splitlines()
    assert lines[0] == "# Everyday News – 2026-10-29"
    assert lines[2] == "_Generated 20:00 · last 24 h · 1 stories from 1 sites · 0 filtered out_"
    headings = [line for line in lines if line.startswith("## ") and "Filtered" not in line]
    assert headings == ["## Hacker News (0)", "## BBC News World (1)", "## WP.pl Wiadomości (0)"]
    assert md.count("_Nothing new._") == 2


def test_entry_with_summary_time_discussion_and_nested_coverage() -> None:
    lead = item(1, "bbc", "What we know so far", "More than 500 passengers. On board.", 9)
    hn = item(2, "hn", "Spain crash", hours_ago=10, discussion="https://news.ycombinator.com/i")
    video = item(3, "bbc", "Watch: scene", hours_ago=26, action="downrank", reason="video")
    md = render(story(1, lead, hn, video))
    assert "- **[What we know so far](https://x/1)**\n  More than 500 passengers. On board.\n" in md
    assert "  _11:00_\n" in md  # 10:00 UTC shown in Warsaw time
    assert (
        "  - also: [Spain crash](https://x/2) · Hacker News · 10:00"
        " · [discussion](https://news.ycombinator.com/i)"
    ) in md
    assert "  - also: [Watch: scene](https://x/3) · BBC News World · 28 Oct 18:00" in md


def test_hn_entry_without_text_has_no_summary_line() -> None:
    md = render(story(1, item(1, "hn", "Toxic Experts", discussion="https://hn/1")))
    assert "- **[Toxic Experts](https://x/1)**\n  _19:00 · [discussion](https://hn/1)_\n" in md


def test_downranked_story_says_why() -> None:
    lead = item(1, "bbc", "Watch: King dances", action="downrank", reason="video")
    assert "_19:00 · downranked: video_" in render(story(1, lead, downranked="video"))


def test_cap_per_site_and_count_of_rest() -> None:
    stories = [story(n, item(n, "bbc", f"Story {n}", "Text.")) for n in range(1, 5)]
    md = render(*stories)
    assert "Story 1" in md and "Story 2" in md and "Story 3" not in md
    assert "_+ 2 more stories not shown_" in md


def test_more_than_three_other_articles_are_counted() -> None:
    others = [item(n, "bbc", f"Other {n}") for n in range(2, 7)]
    md = render(story(1, item(1, "bbc", "Lead"), *others))
    assert md.count("  - also:") == 3
    assert "  - + 2 more" in md


def test_titles_and_summaries_are_escaped() -> None:
    lead = item(1, "wp", "Kaczyński o UE [SKRÓT DNIA]", "Cena *spadła* o 5_%.")
    md = render(story(1, lead))
    assert "**[Kaczyński o UE \\[SKRÓT DNIA\\]](https://x/1)**" in md
    assert "Cena \\*spadła\\* o 5\\_%." in md
    assert escape("a|b<c>#") == "a\\|b\\<c\\>\\#"


def test_stories_from_removed_sources_get_their_own_section() -> None:
    md = render(story(1, item(1, "reddit", "Old Reddit story")))
    assert "## reddit (1)" in md


def test_digest_path_uses_local_date_and_write_creates_directory(tmp_path: Path) -> None:
    late = datetime(2026, 10, 29, 23, 30, tzinfo=UTC)  # already Oct 30 in Warsaw
    path = digest_path(late, tmp_path / "digests", tz=WARSAW)
    assert path == tmp_path / "digests" / "2026-10-30.md"
    write_digest("# x\n", path)
    write_digest("# y\n", path)  # same day: overwritten
    assert path.read_text(encoding="utf-8") == "# y\n"


def test_filtered_section_groups_drops_by_reason_and_tallies_downranks() -> None:
    bait = item(
        1, "wp", "Aż 1,5 mln wyświetleń", hours_ago=3, action="drop", reason="view-count bait"
    )
    szok = item(2, "wp", "Szok!", hours_ago=2, action="drop", reason="sensational")
    more = item(
        3, "wp", "Aż 2 mln wyświetleń", hours_ago=1, action="drop", reason="view-count bait"
    )
    video = item(4, "bbc", "Watch: x", action="downrank", reason="video")
    teaser = item(5, "wp", "Jest nagranie", action="downrank", reason="teaser headline")
    md = render(
        story(1, video, downranked="video"),
        story(2, item(6, "wp", "Plain"), teaser),
        dropped=(more, szok, bait),
    )
    section = md[md.index("## Filtered out (3)") :]
    assert "`filters.toml`" in section
    assert section.index("**view-count bait** (2)") < section.index("**sensational** (1)")
    assert "- [Aż 2 mln wyświetleń](https://x/3) · WP.pl Wiadomości · 19:00" in section
    assert "- [Szok!](https://x/2) · WP.pl Wiadomości · 18:00" in section
    assert "_Downranked but shown: teaser headline 1 · video 1_" in section
    assert "_3 filtered out_" not in md and "· 3 filtered out_" in md


def test_filtered_section_when_nothing_was_filtered() -> None:
    md = render(story(1, item(1, "bbc", "Plain")))
    section = md[md.index("## Filtered out (0)") :]
    assert "_Nothing was filtered out._" in section
    assert "Downranked but shown" not in md
