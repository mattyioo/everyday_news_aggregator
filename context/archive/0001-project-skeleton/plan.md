# 0001 – Plan

## Plan
- [x] Proposal approved

## Build
- [x] `git init` + `.gitignore`
- [x] `python -m venv .venv` + `.venv/bin/pip install uv`
- [x] `pyproject.toml` for `everyday-news`, Python ≥ 3.12, `uv` syncs into `.venv`
- [x] Add deps: `typer`; dev deps: `pytest`, `ruff`, `uv`
- [x] `src/everyday_news/cli.py` with `fetch`, `digest`, `run` stubs
- [x] Register `news` script in `pyproject.toml`
- [x] `tests/test_cli.py` smoke test
- [x] `README.md`

## Verify
- [x] `uv run news --help`
- [x] `uv run pytest` (2 passed)
- [x] `uv run ruff check` + `ruff format --check`
- [x] First git commit

## Archive
- [x] Update `foundation/roadmap.md` status
- [x] Move folder to `archive/`, add index line
