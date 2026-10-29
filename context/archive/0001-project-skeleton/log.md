# 0001 – Log

## 2026-10-29
- Proposed. Waiting for approval.
- Updated for Q5/Q6 answers: git yes; uv installed via pip inside `.venv`.
- Approved. Also swapped WSJ (paywalled) for r/technology in foundation docs.
- Wrote `pyproject.toml` by hand instead of `uv init`, to control layout (src/, hatchling).
- Gotcha: `uv sync` removes packages not in the lockfile, which would uninstall `uv` itself
  from `.venv`. Fixed by listing `uv` in the `dev` dependency group.
- Verified: `news --help` lists fetch/digest/run, pytest 2 passed, ruff clean.
- Archived.
