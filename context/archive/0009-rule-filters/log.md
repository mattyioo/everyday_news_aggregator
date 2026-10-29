# 0009 – Log

## 2026-10-29
- User approved remaining Phase 2 and Phase 3, no questions until done. No muted topics given.
- Reviewed real WP/BBC/HN headlines for teaser, roadmap and promo patterns.
- Rules use regexes on titles (single-quoted TOML literals); muted words reuse the
  prefix-stem matching. Drop beats downrank; first matching rule of that action wins.
- Test caught a stem trap: "celebryt" does not match "celebryci" → config comment now says
  to pick stems short enough for Polish endings ("celebry").
- Real DB (migration 4): 1 drop (view-count bait), 10 downranks (6 WP teasers/roundup,
  3 BBC "Watch:", 1 "Launch HN:"). Reviewed all; no false positives; plain news untouched.
- Tests: 78 passed (24 new). Verified and archived.
