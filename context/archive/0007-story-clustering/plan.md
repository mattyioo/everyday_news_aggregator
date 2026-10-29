# 0007 – Plan

## Plan
- [x] Proposal approved

## Build
- [x] Migration 3: `story`, `story_article`
- [x] `cluster.py`: key words (stopwords EN/PL, prefix stem), title + text scores
- [x] Incremental assignment with rolling 3-day window; leave-on-duplicate; delete empty stories, story title choice
- [x] Wire into `news fetch`; `news stories` command
- [x] Fixture from real titles/leads; tests for the four groups, the trap, language split, window, idempotency

## Verify
- [x] Run on real `news.db`; review every multi-article story by hand
- [x] `uv run pytest`, `uv run ruff check`

## Archive
- [x] Update `foundation/` (architecture, tech-stack: no rapidfuzz), roadmap status
- [x] Move folder to `archive/`, add index line, commit `0007: Story clustering`
