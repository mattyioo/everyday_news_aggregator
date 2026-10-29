# 0001 – Project skeleton

Stage: Archive · Phase 1

## Why

Every later change needs a package to put code in, a CLI to run it, and tests
that run. Doing this once, first, keeps later changes small.

## What

- `git init`, `.gitignore` (`.venv/`, `.env`, `*.db`, `digests/`)
- `python -m venv .venv` and `pip install uv` inside it (nothing installed system-wide)
- `pyproject.toml` managed by `uv`, package at `src/everyday_news/`
- CLI entry point `news` with stub commands: `fetch`, `digest`, `run`
- `pytest` and `ruff` configured; one smoke test for the CLI
- Short `README.md` with setup and run instructions

## Out of scope

Fetching, storage, filtering: anything that does real work.

## Acceptance criteria

- `uv run news --help` lists `fetch`, `digest`, `run`
- `uv run pytest` passes
- `uv run ruff check` passes
- `git status` is clean after the first commit
- No packages installed outside `.venv/`

## Depends on

Q5 (git: yes) and Q6 (uv via pip in `.venv`) in `foundation/decisions.md`: both answered.
