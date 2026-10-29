"""Render the ranked stories as a Markdown digest, one section per site."""

import re
from datetime import datetime, tzinfo
from pathlib import Path

from everyday_news.rank import Item, RankedStory, Ranking
from everyday_news.settings import Settings
from everyday_news.sources import Source
from everyday_news.summarize import story_summary

DEFAULT_DIR = Path("digests")
MAX_ALSO = 3

MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")
MARKDOWN_SPECIAL = re.compile(r"([\\`*_\[\]<>#|])")


def escape(text: str) -> str:
    """Escape characters that Markdown would treat as formatting or links."""
    return MARKDOWN_SPECIAL.sub(r"\\\1", text)


def _when(published: datetime, now: datetime, tz: tzinfo | None) -> str:
    local, today = published.astimezone(tz), now.astimezone(tz)
    if local.date() == today.date():
        return local.strftime("%H:%M")
    return f"{local.day} {MONTHS[local.month - 1]} {local.strftime('%H:%M')}"


def _discussion(item: Item) -> str:
    return f" · [discussion]({item.discussion_url})" if item.discussion_url else ""


def _entry(story: RankedStory, names: dict[str, str], now: datetime, tz: tzinfo | None) -> str:
    lead = story.lead
    lines = [f"- **[{escape(lead.title)}]({lead.url})**"]
    summary = story_summary(story)
    if summary:
        lines.append(f"  {escape(summary)}")

    meta = f"{_when(lead.published, now, tz)}{_discussion(lead)}"
    if story.downranked:
        meta += f" · downranked: {escape(story.downranked)}"
    lines.append(f"  _{meta}_")

    for item in story.others[:MAX_ALSO]:
        site = escape(names.get(item.source_id, item.source_id))
        lines.append(
            f"  - also: [{escape(item.title)}]({item.url}) · {site}"
            f" · {_when(item.published, now, tz)}{_discussion(item)}"
        )
    if len(story.others) > MAX_ALSO:
        lines.append(f"  - + {len(story.others) - MAX_ALSO} more")
    return "\n".join(lines)


def render_digest(
    ranking: Ranking,
    sources: list[Source],
    settings: Settings,
    now: datetime,
    tz: tzinfo | None = None,
) -> str:
    """Markdown for the whole digest. `tz=None` uses the machine's local timezone."""
    names = {s.id: s.name for s in sources}
    by_site: dict[str, list[RankedStory]] = {}
    for story in ranking.stories:
        by_site.setdefault(story.lead.source_id, []).append(story)

    # Configured sites in sources.toml order, then any leftovers (removed sources)
    site_ids = [s.id for s in sources if s.enabled]
    site_ids += sorted(set(by_site) - set(site_ids))

    local_now = now.astimezone(tz)
    out = [
        f"# Everyday News – {local_now:%Y-%m-%d}",
        "",
        f"_Generated {local_now:%H:%M} · last {settings.digest_hours} h · "
        f"{len(ranking.stories)} stories from {len(by_site)} sites · "
        f"{len(ranking.dropped)} filtered out_",
    ]
    for site_id in site_ids:
        stories = by_site.get(site_id, [])
        out += ["", f"## {escape(names.get(site_id, site_id))} ({len(stories)})", ""]
        if not stories:
            out.append("_Nothing new._")
            continue
        shown = stories[: settings.stories_per_site]
        out += [_entry(s, names, now, tz) for s in shown]
        if len(stories) > len(shown):
            out += ["", f"_+ {len(stories) - len(shown)} more stories not shown_"]
    return "\n".join(out) + "\n"


def digest_path(now: datetime, directory: Path = DEFAULT_DIR, tz: tzinfo | None = None) -> Path:
    return directory / f"{now.astimezone(tz):%Y-%m-%d}.md"


def write_digest(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
