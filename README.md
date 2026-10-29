# everyday_news

Personal news aggregator. Pulls Hacker News, BBC News World, WP.pl and
znosnenewsy.pl, filters out the noise, and writes a short daily Markdown digest.

## Setup

Nothing is installed system-wide; `uv` lives inside the project venv.

```sh
python3 -m venv .venv
.venv/bin/pip install uv
.venv/bin/uv sync
```

## Usage

```sh
.venv/bin/uv run news --help
.venv/bin/uv run news sources  # list feeds from sources.toml
.venv/bin/uv run news stories  # same-event stories covered by several articles
.venv/bin/uv run news run      # fetch once, then write digests/YYYY-MM-DD.md
.venv/bin/uv run news digest   # rewrite today's digest from stored news (no network)
.venv/bin/uv run news top      # ranked stories with score parts
.venv/bin/uv run news follow 15 # follow story #15 (ids are in the digest); unfollow / following
```

## Development

```sh
.venv/bin/uv run pytest
.venv/bin/uv run ruff check
```

Noise rules and muted words live in `filters.toml`.
Topics to follow live in `follow.toml`.
Feeds are configured in `sources.toml`; `settings.toml` sets how long news is kept
(`retention_days`, currently 7 days after an article leaves its feed).

Project plans and change history live in `context/` (see `context/README.md`).
