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
| 0008-retention | 2 | 2026-10-29 | Delete articles 30 days after last seen in their feed (`settings.toml`), at launch |
