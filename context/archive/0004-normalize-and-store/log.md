# 0004 – Log

## 2026-10-29
- Proposed and approved as part of the Phase 1 go-ahead.
- Inspected raw summaries of all four sources in `news.db` to design the rules.
- Renamed planned `content_hash` to `title_hash`: hash of the normalized title,
  which is what exact-duplicate detection (0005) will compare. Canonical URL covers the URL side.
- Rules key off feed shape (`[link]` anchor, `comments` field, WordPress footers),
  not source ids, so another subreddit or WordPress site works unchanged.
- Raw items whose source isn't in `sources.toml` stay pending instead of being dropped.
- Real DB: 55 articles (hn 30, wp 15, znosnenewsy 10), no HTML/entities, HN 29/30 with
  discussion link (the other is an HN-internal item). Second run: 0 new.
- Reddit is only verified against the fixture: the real fetch is still in backoff after 0003's 429.
- Verified and archived.
