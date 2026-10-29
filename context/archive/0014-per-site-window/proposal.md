# 0014 – Per-site digest window

Stage: Archive · Phase 4

## Why

Znośne Newsy posts a few items a week, so the 24 h digest window usually shows
"Nothing new" for it. The user asked to give it a longer window.

## What

- Optional `digest_hours` per source in `sources.toml`, overriding `settings.toml`'s
  `digest_hours` for that site. Validated like the global one (1–720).
- `znosnenewsy`: `digest_hours = 168` (7 days, same as retention).
- Ranking: an article is "in the window" when it is newer than its **own site's** window;
  a story is listed when any kept article is in its window. The dropped list uses the same rule.
- Digest header says which sites use a different window.

## Acceptance criteria

- Real digest: Znośne Newsy section lists its recent posts instead of "Nothing new"
- Other sites unchanged (24 h)
- pytest + ruff pass

## Approval

User request, together with the Phase 4 go-ahead (2026-10-29).
