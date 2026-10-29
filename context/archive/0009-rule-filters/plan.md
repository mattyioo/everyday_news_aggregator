# 0009 – Plan

## Plan
- [x] Proposal approved (Phase 2 + 3 go-ahead)

## Build
- [x] `filters.toml` with starting rules
- [x] `filters.py`: load/validate, evaluate article, `apply_filters(conn, config)`
- [x] Migration 4: `article_verdict`
- [x] Wire into `news fetch`
- [x] Tests: real headlines, muted words, lang scoping, config errors, recompute after edit

## Verify
- [x] Real DB: review every verdict by hand
- [x] `uv run pytest`, `uv run ruff check`

## Archive
- [x] Docs, roadmap, archive index, commit `0009: Rule filters`
