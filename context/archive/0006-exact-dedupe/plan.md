# 0006 – Plan

## Plan
- [x] Proposal approved

## Build
- [x] `user_version` migrations in `db.py`; migration 1 adds `article.duplicate_of`
- [x] `dedupe.py`: group by url and by (lang, title_hash); pick primary; mark others
- [x] Wire into `news fetch`, add count to summary
- [x] Tests: same url cross-source, same title same/different lang, primary choice, idempotent, migration of an old DB

## Verify
- [x] Run on real `news.db` (0 requests needed: `news fetch` within cooldown)
- [x] `uv run pytest`, `uv run ruff check`

## Archive
- [x] Update `foundation/architecture.md` data model, roadmap status
- [x] Move folder to `archive/`, add index line, commit `0006: Exact dedupe`
