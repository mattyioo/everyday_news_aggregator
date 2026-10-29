# 0002 – Log

## 2026-10-29
- Proposed. Waiting for approval.
- Approved. User asked that requests must not look like spam and that the app
  refreshes only once, when it is launched. Recorded in `foundation/decisions.md`
  and `architecture.md`; scheduled runs (0014) dropped. Fetching rules are applied in 0003.
- Added an `id` field per source (short stable key for the database later).
- `fetch_fulltext` is false for all sources: full-text fetching is one request per
  article, the pattern we want to avoid.
- `.env` question answered: kept in `.gitignore` but unused, no secrets needed.
- ruff B008 flagged `typer.Option` as a default; switched to `Annotated[...]`.
- Verified and archived.
