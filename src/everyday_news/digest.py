"""Render the ranked stories as a Markdown digest, one section per site."""

import re
from collections import Counter
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


BADGES = {"new": "🆕 ", "updated": "🔄 "}


def story_status(story: RankedStory, since: datetime | None) -> str | None:
    """ "new" (every article arrived after `since`), "updated" (some did), else None."""
    if since is None:
        return None
    fresh = [i for i in story.items if i.fetched > since]
    if not fresh:
        return None
    return "new" if len(fresh) == len(story.items) else "updated"


def _entry(
    story: RankedStory,
    names: dict[str, str],
    now: datetime,
    tz: tzinfo | None,
    since: datetime | None,
) -> str:
    lead = story.lead
    status = story_status(story, since)

    def fresh(item: Item) -> str:
        return " · new" if status == "updated" and item.fetched > since else ""

    lines = [f"- {BADGES.get(status, '')}**[{escape(lead.title)}]({lead.url})**"]
    summary = story_summary(story)
    if summary:
        lines.append(f"  {escape(summary)}")

    meta = f"{_when(lead.published, now, tz)}{_discussion(lead)}{fresh(lead)}"
    if story.downranked:
        meta += f" · downranked: {escape(story.downranked)}"
    lines.append(f"  _{meta} · \\#{story.id}_")

    for item in story.others[:MAX_ALSO]:
        site = escape(names.get(item.source_id, item.source_id))
        lines.append(
            f"  - also: [{escape(item.title)}]({item.url}) · {site}"
            f" · {_when(item.published, now, tz)}{_discussion(item)}{fresh(item)}"
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
    since: datetime | None = None,
) -> str:
    """Markdown for the whole digest. `tz=None` uses the machine's local timezone;
    `since` (the previous visit, see visits.baseline) enables new/updated markers."""
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
    longer = [
        f"{escape(s.name)} {s.digest_hours} h"
        for s in sources
        if s.enabled and s.digest_hours and s.digest_hours != settings.digest_hours
    ]
    if longer:
        out += ["", f"_Own window: {', '.join(longer)}_"]
    if since is None:
        out += ["", "_First digest: nothing earlier to compare with._"]
    else:
        statuses = [story_status(s, since) for s in ranking.stories]
        out += [
            "",
            f"_{statuses.count('new')} new · {statuses.count('updated')} updated "
            f"since your last digest ({_when(since, now, tz)})_",
        ]
    for site_id in site_ids:
        stories = by_site.get(site_id, [])
        out += ["", f"## {escape(names.get(site_id, site_id))} ({len(stories)})", ""]
        if not stories:
            out.append("_No stories in the window._")
            continue
        # New and updated first (each still by score), so the cap cuts seen stories first
        stories.sort(key=lambda s: story_status(s, since) is None)
        shown = stories[: settings.stories_per_site]
        out += [_entry(s, names, now, tz, since) for s in shown]
        if len(stories) > len(shown):
            out += ["", f"_+ {len(stories) - len(shown)} more stories not shown_"]
    out += _filtered_section(ranking, names, now, tz)
    return "\n".join(out) + "\n"


def _filtered_section(
    ranking: Ranking, names: dict[str, str], now: datetime, tz: tzinfo | None
) -> list[str]:
    """What the filters hid (with links) and a tally of what they only downranked."""
    out = ["", f"## Filtered out ({len(ranking.dropped)})", ""]
    out.append("_Hidden by rules in `filters.toml`; edit it if something here should stay._")

    by_reason: dict[str, list[Item]] = {}
    for item in ranking.dropped:
        by_reason.setdefault(item.reason or "unknown", []).append(item)
    if not by_reason:
        out += ["", "_Nothing was filtered out._"]
    for reason, items in sorted(by_reason.items(), key=lambda kv: (-len(kv[1]), kv[0])):
        out += ["", f"**{escape(reason)}** ({len(items)})", ""]
        out += [
            f"- [{escape(i.title)}]({i.url}) · {escape(names.get(i.source_id, i.source_id))}"
            f" · {_when(i.published, now, tz)}"
            for i in items
        ]

    downranked = Counter(
        i.reason for s in ranking.stories for i in s.items if i.action == "downrank"
    )
    if downranked:
        ordered = sorted(downranked.items(), key=lambda kv: (-kv[1], kv[0] or ""))
        tally = " · ".join(f"{escape(r or 'unknown')} {n}" for r, n in ordered)
        out += ["", f"_Downranked but shown: {tally}_"]
    return out


def digest_path(now: datetime, directory: Path = DEFAULT_DIR, tz: tzinfo | None = None) -> Path:
    return directory / f"{now.astimezone(tz):%Y-%m-%d}.md"


def write_digest(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
