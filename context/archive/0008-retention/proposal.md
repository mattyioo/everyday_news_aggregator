# 0008 – Retention

Stage: Archive · Phase 2

## Why

Nothing is ever deleted today. Size is not the real problem (~100 articles/day is about
1 MB/month), but an ever-growing database slows dedupe and clustering (they look at
every row) and keeps news nobody will read again.

## What

- **Articles are deleted 30 days after they were last seen in their site's feed.**
  Deletion runs at launch inside `news fetch` (after fetching, no extra requests);
  nothing runs in the background.
- `settings.toml` (new, user-editable): `retention_days = 30`. Invalid value → clear error.
- **"Last seen", not publish date.** Some feeds keep items for weeks (znosnenewsy lists
  an item from 2026-10-15). Deleting by publish date while the item is still in the feed
  would make the next fetch import it again as *new*.
  - Migration 2: `raw_item.last_seen_at`, backfilled from `fetched_at`.
  - On `200`: every item in the response gets `last_seen_at = now`.
  - On `304 Not Modified`: the feed is unchanged, so the items seen in the previous
    successful fetch (those with that source's latest `last_seen_at`) are bumped to now.
  - Skipped/failed fetches bump nothing.
- Deleted together: the raw item and its article. Duplicate links are repaired by the
  dedupe step that runs right after.
- `fetch_state` rows of sources no longer in `sources.toml` are deleted too.
- `news fetch` summary line gains `, N deleted`.
- Digest files (future `digests/*.md`) are never deleted.
- Story clustering (0007, not built yet) must delete stories left with no articles; noted there.

## Out of scope

`VACUUM` (SQLite reuses freed space; the file stops growing once retention kicks in).
Followed stories (Phase 4 will exempt them from deletion).

## Acceptance criteria

- An article unseen for 30+ days is deleted with its raw item; one still in the feed
  (or behind a `304`) is kept however old
- A deleted item that is still in a feed is not re-imported as new (covered by last-seen)
- `retention_days` read from `settings.toml`; bad value → error, exit 1
- Existing `news.db` migrates in place
- pytest + ruff pass

## Approval

User approved automatic deletion on 2026-10-29.
