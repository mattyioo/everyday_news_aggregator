# Conventions

## Code

- Source lives in `src/everyday_news/`, tests in `tests/`.
- Type hints on all public functions.
- Small modules, one pipeline step per module (`fetch.py`, `normalize.py`, ...).
- No network calls in tests; use saved feed fixtures in `tests/fixtures/`.
- `ruff check` and `pytest` must pass before a change moves to **Verify**.
- Run tools through the venv: `.venv/bin/uv run <cmd>`. Keep `uv` in the `dev` group so `uv sync` doesn't uninstall it.
- One git commit per change, made when it is archived. Message: `NNNN: <change title>`.

## Secrets

- API keys come from environment variables (or a gitignored `.env`). Never committed, never logged.

## Context docs

- Markdown only.
- Change folders: `NNNN-short-slug`, numbered in order, never reused.
- One change = one coherent outcome. If a change grows past ~1 day of work, split it.
- Every code change belongs to a change folder; no untracked work.
- Dates in logs use `YYYY-MM-DD`.
