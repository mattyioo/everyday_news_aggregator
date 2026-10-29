# Archive

Finished changes, moved here from `context/change/`. Not edited after archiving.

| Change | Phase | Archived | Outcome |
|---|---|---|---|
| 0000-context-system | 0 | 2026-10-29 | Context folders, foundation docs, roadmap, CLAUDE.md |
| 0001-project-skeleton | 1 | 2026-10-29 | git, `.venv` with uv, package, `news` CLI stubs, pytest + ruff |
| 0002-sources-config | 1 | 2026-10-29 | `sources.toml` (HN, r/technology, WP.pl, znosnenewsy.pl), validated loader, `news sources` |
| 0003-feed-fetcher | 1 | 2026-10-29 | Polite fetcher: UA, conditional GET, cooldown + error backoff, no retries/redirects; `news fetch` |
| 0004-normalize-and-store | 1 | 2026-10-29 | `article` table: clean text, canonical URLs, discussion links, title hash; runs inside `news fetch` |
| 0005-replace-reddit-with-bbc | 1 | 2026-10-29 | Reddit (rate-limited) replaced by BBC News World; BBC tracking params stripped |
| 0006-exact-dedupe | 2 | 2026-10-29 | `duplicate_of` via url / (lang, title) groups, highest-weight primary; schema migrations |
| 0007-story-clustering | 2 | 2026-10-29 | `story` tables; same-event grouping per language, rolling 3-day window, stable ids; `news stories` |
| 0008-retention | 2 | 2026-10-29 | Delete articles 30 days after last seen in their feed (`settings.toml`), at launch |
| 0009-rule-filters | 2 | 2026-10-29 | `filters.toml`: muted words + EN/PL headline rules (drop/downrank) with reasons |
| 0010-heuristic-scoring | 2 | 2026-10-29 | `rank.py`: weight × recency × coverage × downrank, lead article choice, `digest_hours`, `news top` |
| 0011-summaries | 3 | 2026-10-29 | Extractive summaries: whole sentences ≤ 280 chars, EN/PL abbreviation-aware |
| 0012-markdown-digest | 3 | 2026-10-29 | `news digest` / `news run` write `digests/YYYY-MM-DD.md`, one section per site |
| 0013-filtered-report | 3 | 2026-10-29 | Digest ends with dropped articles by reason (links) and a downrank tally |
| 0014-per-site-window | 4 | 2026-10-29 | Optional per-source `digest_hours`; Znośne Newsy 7 days |
| 0015-whats-new | 4 | 2026-10-29 | 🆕/🔄 markers since the last digest (by fetch time), new first per site, story ids |
| 0016-followed-topics | 4 | 2026-10-29 | Follow stories (`news follow`) and topics (`follow.toml`); Following section shows only updates |
| 0017-bbc-host-alias | 5 | 2026-10-29 | bbc.com = bbc.co.uk in canonical URLs; primary prefers text; borrowed HN discussion link |
| 0018-web-view | 5 | 2026-10-29 | `news web`: fetch once, then browse digests at 127.0.0.1:8765 |
