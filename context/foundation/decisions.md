# Decisions

## Open questions

Need answers before the change that depends on them.

| # | Question | Default if unanswered | Needed by |
|---|---|---|---|
| — | none open | | |

## Decision log

| Date | Decision | Why |
|---|---|---|
| 2026-10-29 | Context lives in `context/` with `foundation/`, `change/`, `archive/`, Markdown only | User-defined workflow |
| 2026-10-29 | Every change goes through Propose → Plan → Build → Verify → Archive | Predictable, reviewable steps |
| 2026-10-29 | Python + SQLite, local-only, single user | Simplest stack that fits the problem |
| 2026-10-29 | Q1 Sources: Hacker News, WSJ, WP.pl (Wiadomości), znosnenewsy.pl (feeds in `tech-stack.md`) | User choice |
| 2026-10-29 | WSJ dropped (paywalled), replaced with Reddit r/technology | User choice |
| 2026-10-29 | Q2 No LLM anywhere. Filtering, scoring and summaries are rule/heuristic based | User choice |
| 2026-10-29 | Q3 Digest output is a Markdown file | User choice |
| 2026-10-29 | Q4 English and Polish. Language is set per source in config, not detected | User choice; every source is single-language |
| 2026-10-29 | Q5 Project is a git repo | User choice |
| 2026-10-29 | Q6 `uv` is installed with `pip` inside the project venv `.venv/`, not system-wide | User choice |
