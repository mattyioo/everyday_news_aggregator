# 0005 – Replace Reddit with BBC News World

Stage: Archive · Phase 1

## Why

Reddit's feed for logged-out apps is rate-limited too hard to rely on (429 after a
handful of requests during 0003). The user dropped it. Without it the only English
source is Hacker News (tech only), so a general world-news source fills the gap WSJ left.

## What

- `sources.toml`: remove `reddit-technology`, add `bbc`:
  BBC News World, `https://feeds.bbci.co.uk/news/world/rss.xml`, `en`, weight 1.0, tags `general`, `world`
- Strip BBC's tracking params (`at_medium`, `at_campaign`) in `canonical_url`
- BBC fixture (trimmed real feed) + tests
- Reddit-format normalization stays (generic `[link]` rule, still tested by the Reddit
  fixture) so a subreddit can be re-added later without code changes
- Update foundation docs (sources table, decisions, roadmap: Phase 2 renumbered +1)

## Out of scope

Removing Reddit's `fetch_state` row from an existing `news.db` (harmless, never read again).

## Acceptance criteria

- `news sources` lists hn, bbc, wp, znosnenewsy
- A real `news fetch` stores BBC articles with clean URLs (no `at_*` params)
- Phase 1 exit holds for every configured source
- pytest + ruff pass

## Approval

User chose BBC News World on 2026-10-29 and asked to proceed.
