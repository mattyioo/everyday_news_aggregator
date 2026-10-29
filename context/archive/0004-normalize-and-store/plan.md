# 0004 – Plan

## Plan
- [x] Proposal approved (Phase 1 approval)

## Build
- [x] `article` table in `db.py` (+ indexes on title_hash, published_at)
- [x] HTML → text helper (stdlib `html.parser`)
- [x] `Article`, `normalize_item()`, URL canonicalization, title hash
- [x] `normalize_pending(conn, sources)`
- [x] Call it from `news fetch`, print count
- [x] Tests per source fixture + idempotency + URL cleanup

## Verify
- [x] Normalize the real `news.db` (0 new requests): 55 articles, no HTML left
- [x] `uv run pytest` (30 passed), `uv run ruff check`

## Archive
- [x] Update `foundation/architecture.md` data model, roadmap status
- [x] Move folder to `archive/`, add index line, commit `0004: Normalize and store`
- [x] Phase 1 exit check
