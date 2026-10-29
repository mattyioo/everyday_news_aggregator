# 0006 – Exact dedupe

Stage: Archive · Phase 2

## Why

The same article can arrive twice: a Hacker News post linking to a BBC article that
is also in the BBC feed (same URL), or a site republishing an item under a new id
(same title). The digest should show it once.

Checked on the real `news.db` (82 articles): 0 exact duplicates today, so this is
mostly about what accumulates across days and sources. Kept deliberately small.

## What

- `article.duplicate_of` (nullable article id). `NULL` = this article is shown.
- An article is a duplicate when another article has
  - the same canonical `url`, or
  - the same `title_hash` **and** the same `lang`
- Which one stays primary: highest source `weight`, then earliest `published_at`, then lowest id.
  The duplicate keeps its row, so its `discussion_url` (e.g. the HN thread) can be shown
  next to the primary later ("also discussed on Hacker News").
- `src/everyday_news/dedupe.py`: `mark_duplicates(conn, sources) -> int`, idempotent,
  runs in `news fetch` after normalize (no requests).
- Tiny schema migration: `PRAGMA user_version` in `db.py`, so the existing `news.db`
  gets the new column instead of having to be deleted.
- `news fetch` summary line gains `, N duplicate(s)`.

## Out of scope

Near-duplicates and same-event grouping (0007 clustering). Cross-language matching.

## Acceptance criteria

- Same URL from two sources → one primary, one `duplicate_of` it; primary is the higher-weight source
- Same title + same lang → duplicate; same title in different langs → not
- Running twice changes nothing
- Existing `news.db` migrates in place, no data lost
- pytest + ruff pass
