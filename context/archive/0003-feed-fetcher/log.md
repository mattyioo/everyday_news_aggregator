# 0003 – Log

## 2026-10-29
- Proposed. Approved together with the rest of Phase 1.
- Fixture download found `znosnenewsy.pl/feed` answers 301 → `/feed/`. Fixed the URL
  in `sources.toml`; the client does not follow redirects (a redirect is a 2nd request).
- Only znosnenewsy sends ETag / Last-Modified. HN, Reddit and WP don't, so for them
  the cooldown is what prevents repeat requests.
- HN items have no `<guid>`: link is used as guid; HN discussion link kept in `comments_url`.
- `Server` test helper uses `httpx.MockTransport` via a `transport` param on `make_client`.
- Real run 1: hn 30, wp 15, znosnenewsy 10 items; reddit 403. Run 2: 0 requests (cooldown).
- Reddit diagnosis (one request): 429 with `x-ratelimit-remaining: 0`. Reddit rate-limits
  unauthenticated feed requests hard; ~6 dev requests in ~30 min exhausted it.
  App behaved correctly (skip, no retry). Added `ERROR_COOLDOWN` = 60 min after any
  failed fetch so a struggling site hears from us even less.
- Follow-up to watch: if Reddit keeps failing at normal once-per-launch use, consider
  Reddit's preferred UA format (`linux:everyday_news:0.1.0 (by /u/<name>)`) or drop it.
- Verified and archived.
