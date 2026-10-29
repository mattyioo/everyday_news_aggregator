# 0016 – Plan

## Plan
- [x] Proposal approved (Phase 4 go-ahead)

## Build
- [x] `keywords.py` shared stem matching; filters use it
- [x] Migration 6 `followed_story`; `follow.py`: follow/unfollow/list, `follow.toml` topics
- [x] `rank.py`: load stories by id (no window)
- [x] Cluster: 30-day window for followed stories, clean dangling follows
- [x] Prune: skip followed stories
- [x] Digest: Following section; exclude shown stories from site sections
- [x] CLI: follow / unfollow / following; digest wiring
- [x] Tests

## Verify
- [x] Real: follow a story, run twice, check only updates show
- [x] `uv run pytest`, `uv run ruff check`

## Archive
- [x] Docs, README, roadmap (Phase 4 done), archive index, commit `0016: Followed stories and topics`
