# everyday_news

Personal news aggregator. Pulls Hacker News, r/technology, WP.pl and
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
.venv/bin/uv run news run      # fetch + digest
```

## Development

```sh
.venv/bin/uv run pytest
.venv/bin/uv run ruff check
```

Project plans and change history live in `context/` (see `context/README.md`).
