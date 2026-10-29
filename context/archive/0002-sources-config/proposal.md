# 0002 – Sources config

Stage: Archive · Phase 1

## Why

The fetcher (0003) needs to know what to fetch. Sources should be edited in one
human-readable file, not in code.

## What

- `sources.toml` at the project root with the four sources:

  | name | lang | url | weight |
  |---|---|---|---|
  | Hacker News | en | `https://news.ycombinator.com/rss` | 1.0 |
  | Reddit r/technology | en | `https://www.reddit.com/r/technology/.rss` | 0.8 |
  | WP.pl Wiadomości | pl | `https://wiadomosci.wp.pl/rss.xml` | 0.7 |
  | Znośne Newsy | pl | `https://znosnenewsy.pl/feed` | 1.0 |

  Each entry also has `tags`, `enabled` and `fetch_fulltext`.
- `src/everyday_news/sources.py`: loads and validates the file into `Source` objects
  (stdlib `tomllib` + dataclass; clear error on a missing field or bad `lang`).
- `news sources` CLI command that lists configured sources.

## Out of scope

Network access. Nothing is fetched in this change.

## Acceptance criteria

- `uv run news sources` prints the four sources with language and enabled state
- Invalid config (missing `url`, `lang` not `en`/`pl`) fails with a readable message
- Tests cover valid load, disabled source, and both error cases; pytest + ruff pass
