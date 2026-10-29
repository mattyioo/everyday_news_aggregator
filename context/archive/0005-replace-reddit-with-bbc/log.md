# 0005 – Log

## 2026-10-29
- User dropped Reddit. Checked 5 candidates (1 request each): BBC World, Ars Technica,
  Guardian World, Lobsters OK; AP News 403. User picked BBC News World.
- BBC fixture saved (trimmed to 3 items). Links carry `at_medium=RSS&at_campaign=rss`;
  guid is the link with `#0`. Summaries are plain text.
- Kept the Reddit fixture and the generic `[link]` rule (still tested) so a subreddit can come back without code.
- Tests: 31 passed (BBC added to fetch/normalize suites, new BBC tracking-param test).
- Real fetch: bbc 200, 27 new articles, 0 URLs with query params; others in cooldown (1 request total).
  All four configured sources have now fetched successfully: Phase 1 exit met.
- Verified and archived.
