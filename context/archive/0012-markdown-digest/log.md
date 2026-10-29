# 0012 – Log

## 2026-10-29
- Proposed under the Phase 2 + 3 go-ahead.
- `stories_per_site = 10` added to `settings.toml`. `news digest` reads the DB only;
  `news run` = fetch + digest; `--out` for the directory.
- Meta line first used `<sub>` HTML; switched to plain italics so every Markdown viewer
  renders it.
- Real digest (24 h): HN 25 (10 shown), BBC 23 (10 shown), WP 17 (10 shown),
  znosnenewsy "Nothing new" (slow site). Spain crash once under BBC, led by the explainer,
  HN + video nested; local (Warsaw) times; `[SKRÓT DNIA]` escaped.
- Follow-up noticed: HN links BBC as `bbc.com`, the BBC feed uses `bbc.co.uk` for the same
  article, so exact dedupe misses it (clustering still nests it). Candidate for a later
  host-alias rule in `canonical_url`.
- Tests: 108 passed (9 new). Verified and archived.
