# 0003 – Plan

## Plan
- [x] Proposal approved

## Build
- [x] Add deps: `httpx`, `feedparser`
- [x] `db.py`: open `news.db`, create `fetch_state` + `raw_item`
- [x] `fetch.py`: polite client (User-Agent, timeout, conditional headers, no redirects)
- [x] Cooldown check + `--force`
- [x] Longer backoff (60 min) after a failed fetch (added during Verify)
- [x] Parse with feedparser, insert raw items (`INSERT OR IGNORE` on source + guid)
- [x] Per-source result line + request count; failures isolated
- [x] Wire into `news fetch` / `news run` (`--config`, `--db`)
- [x] Save one real feed sample per source as test fixtures (trimmed to 3 items)
- [x] Tests: 200, 304 + conditional headers, 429/503/301, timeout, cooldown, backoff, force, disabled, no duplicate rows

## Verify
- [x] Real run: 4 requests, then second run 0 requests
- [x] `uv run pytest` (20 passed), `uv run ruff check`

## Archive
- [x] Update `foundation/` docs, roadmap status
- [x] Move folder to `archive/`, add index line, commit `0003: Feed fetcher`
