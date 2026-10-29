# 0012 – Markdown digest

Stage: Archive · Phase 3

## Why

The digest is the product: one Markdown file a day, readable in under 10 minutes.

## What

- `news digest` writes `digests/YYYY-MM-DD.md` (local date; rerunning the same day
  overwrites it) from the database only, no network. `news run` = `news fetch` + `news digest`.
- `src/everyday_news/digest.py`: `render_digest(ranking, sources, settings, now)` → Markdown.
- Layout:
  - header: date, generation time, window, counts
  - **one section per site** (decision: no topic categories), in `sources.toml` order;
    a story goes in the section of its lead article; empty site → "Nothing new."
  - per story: bold linked title, extractive summary (0011), a meta line with local
    time, HN/Reddit discussion link, downrank reason if any; other articles of the
    story nested below ("also: …" with their site and links), at most 3
  - at most `stories_per_site` stories per site (new setting, default 10), then
    "+ N more" so the reader knows something was cut
- Markdown in titles escaped (`[SKRÓT DNIA]` must not break links).
- Times shown in the machine's local timezone (Poland), `HH:MM` today, `D Mon HH:MM` otherwise.

## Out of scope

The "filtered out" section (0013). HTML output.

## Acceptance criteria

- Real data: file written, every enabled site has a section, Spain crash appears once
  (under BBC) with the HN article nested, `[SKRÓT DNIA]` title renders as a link
- `news run` fetches then writes the digest
- pytest + ruff pass

## Approval

Part of the Phase 2 + 3 go-ahead (2026-10-29).
