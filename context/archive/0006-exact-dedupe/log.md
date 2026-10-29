# 0006 – Log

## 2026-10-29
- Proposed. Real DB has 0 exact duplicates across 82 articles; the BBC/WP Brazil story
  is a cross-language same-event case, which is clustering territory, not exact dedupe.
- Approved. User confirmed EN/PL stories may be grouped separately (logged in decisions).
- Union-find groups so URL and title matches chain (A~B by url, B~C by title → one group).
- Full recompute on every run (cheap at this size); only changed rows are updated.
  Lets a better primary (e.g. BBC arriving after an HN link to it) take over.
- Articles from sources no longer in `sources.toml` get weight 0, so they never win.
- Migrations: `MIGRATIONS` list + `PRAGMA user_version`, each applied in one transaction.
- Tests: 38 passed (7 new: cross-source url, same/different-lang title, chaining,
  idempotency + primary reassignment, unconfigured source, old-DB migration).
- Real DB: user_version 0 → 1, 82 articles kept, 3 new fetched (hn 2, wp 1),
  znosnenewsy answered 304 (conditional GET confirmed live). 0 duplicates, as expected.
- Verified and archived.
