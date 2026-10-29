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
| 2026-10-29 | Fetch only when the user starts the app: one refresh per launch, no background polling, no auto-refresh, no scheduled runs | User choice: requests must not look like spam |
| 2026-10-29 | Polite fetching: honest User-Agent, one request per feed per run, sequential with a pause between hosts, conditional GET (ETag / Last-Modified), timeouts, no retry loops, back off on 429. No full-text page fetching by default | Same |
| 2026-10-29 | Scheduled-runs change dropped; it contradicts refresh-on-launch | Follows from the above |
| 2026-10-29 | `.env` stays gitignored but is unused: no secrets are needed (no LLM, public feeds) | No API keys in the project |
| 2026-10-29 | Fetch cooldown 15 min per source; 60 min after a failed fetch. `--force` skips the cooldown only | Relaunching must not resend requests; failing sites get extra quiet time |
| 2026-10-29 | HTTP client never follows redirects; feed URLs must be the final URL | A redirect doubles the requests |
| 2026-10-29 | Reddit r/technology dropped (unauthenticated feed rate-limited too hard); replaced by BBC News World | User choice from BBC / Ars Technica / Guardian / Lobsters |
| 2026-10-29 | English and Polish stories are grouped separately; no cross-language matching | User confirmed; matching across languages would need translation or an LLM |
| 2026-10-29 | No topic categories. News is grouped only by site (source); the digest has one section per site | User choice; keyword categories were tried (uncommitted) and dropped |
| 2026-10-29 | Retention: articles are deleted 30 days after they were last seen in their feed, at launch | User approved automatic deletion; last-seen (not publish date) avoids re-importing items still in a feed |
