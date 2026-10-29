# 0008 – Plan

## Plan
- [x] Proposal approved

## Build
- [x] `settings.toml` + `settings.py` loader (`retention_days`)
- [x] Migration 2: `raw_item.last_seen_at`, backfill from `fetched_at`
- [x] Fetch: set `last_seen_at` on 200 (new + existing items), bump on 304
- [x] `prune.py`: delete unseen raw items + articles; drop stale `fetch_state`
- [x] Wire into `news fetch` (fetch → prune → normalize → dedupe), `--settings` option
- [x] Tests: settings errors, last-seen on 200/304, prune boundary, kept-while-in-feed, migration

## Verify
- [x] Real `news.db` migrates; nothing deleted yet (all data < 30 days old)
- [x] `uv run pytest`, `uv run ruff check`

## Archive
- [x] Update `foundation/` docs, roadmap, archive index, commit `0008: Retention`
