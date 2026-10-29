# 0002 – Plan

## Plan
- [x] Proposal approved

## Build
- [x] `sources.toml` with the four sources (all `fetch_fulltext = false`)
- [x] `Source` dataclass + `load_sources(path)` in `sources.py`
- [x] Validation errors with file/field in the message (missing field, bad lang, bad url, weight range, duplicate id)
- [x] `news sources` command (`--config` to point at another file)
- [x] Tests in `tests/test_sources.py`

## Verify
- [x] `uv run news sources` lists the four sources
- [x] Bad config exits 1 with a readable message
- [x] `uv run pytest` (9 passed), `uv run ruff check`, `ruff format --check`

## Archive
- [x] Update `foundation/roadmap.md` status
- [x] Move folder to `archive/`, add index line, commit `0002: Sources config`
