# 0008 – Log

## 2026-10-29
- User asked how long news is kept: forever so far. Proposed 30 days by last-seen date.
- Keyword topic categories were built (uncommitted) and then dropped by the user:
  `git reset --hard a2534c7`, category files deleted, the `category` column dropped from
  the local `news.db` and `user_version` set back to 1 so this change's migration is #2.
  Number 0008 was free (never committed), so retention takes it.
- User: group only by site. No code needed; recorded in decisions, digest = one section per site.
- Retention approved. Dropped VACUUM from scope (not needed once the DB stops growing).
- Fetch sets `last_seen_at` for every item in a 200 response (new or existing); a 304
  bumps the items from the source's latest successful fetch; errors bump nothing.
- Order in `news fetch`: fetch → prune → normalize → dedupe (dedupe repairs pointers to
  deleted primaries).
- Tests: 47 passed (9 new: boundary at 30 days, kept while in feed, 304 counts as seen,
  failure doesn't, only gone items deleted, stale fetch_state, migration backfill, settings).
- Real DB: user_version 1 → 2, 89 raw items all backfilled, reddit fetch_state removed,
  znosnenewsy 304 bumped its 10 items, 0 deleted (all data < 30 days old).
- Verified and archived.
