# 0003 – Feed fetcher

Stage: Archive · Phase 1

## Why

Get the latest items from the four feeds into a local database, once per app
launch, in a way that no site would treat as spam or a bot attack.

## What

- `src/everyday_news/fetch.py`: fetch every enabled source **once** per run.
- Polite fetching rules (from `foundation/decisions.md`):
  - Honest User-Agent: `everyday_news/0.1 (personal news reader; one fetch per launch)`
  - Sequential requests, 2 s pause between sources, 15 s timeout
  - Conditional GET: send `If-None-Match` / `If-Modified-Since` from the last run;
    a `304 Not Modified` costs the site almost nothing
  - **Cooldown**: if a source was fetched less than 15 minutes ago, skip it and use
    stored items, so relaunching the app several times doesn't send new requests
  - No retries. On 429 / 5xx / timeout, skip that source for this run and say so
  - No background loops, no timers: requests only happen inside `news fetch` / `news run`
- SQLite database `news.db` (gitignored):
  - `fetch_state`: source_id, last_fetched_at, etag, last_modified, last_status
  - `raw_item`: source_id, guid, url, title, summary, published, fetched_at (unique on source_id + guid)
- `news fetch` prints one line per source: `hn  200  30 items (12 new)` / `wp  304  not modified` / `reddit-technology  skipped: cooldown`
- `--force` flag to ignore the cooldown (still one request per source)

## Out of scope

Normalizing into `Article`, dedupe, digest. Full-text page fetching.

## Acceptance criteria

- `news fetch` makes at most 4 HTTP requests (one per source), then exits
- A second `news fetch` within 15 min makes 0 requests
- Re-fetching doesn't duplicate rows in `raw_item`
- One source failing doesn't stop the others
- Tests use saved feed fixtures and a mocked HTTP client: no network in tests
- pytest + ruff pass
