# everyday_news

Personal news aggregator: fetches the feeds in `sources.toml` (currently Hacker News,
BBC News World, WP.pl, znosnenewsy.pl) when the app is launched with `news web` /
`news run` / `news fetch`, filters out noise, merges duplicates, groups same-event
articles into stories, and writes a daily Markdown digest (also viewable in the
browser). Other commands only read stored data. Python, SQLite, no LLM.

## Start here

1. Read `context/README.md` for how the workflow works.
2. Read `context/foundation/roadmap.md` to see the current phase.
3. Open the active change in `context/change/` (if any) and continue from its stage.

## Commands

Everything runs through the project venv; nothing is installed system-wide.

```sh
.venv/bin/uv run news web            # the app: fetch once, write digest, serve 127.0.0.1:8765
.venv/bin/uv run news run            # fetch once + write digests/YYYY-MM-DD.md
.venv/bin/uv run news fetch          # fetch only; --force skips the cooldown (only command with it)
.venv/bin/uv run news digest         # rewrite today's digest, no network
.venv/bin/uv run news top            # ranking with score parts
.venv/bin/uv run news follow <id>    # also: unfollow, following, stories, sources
.venv/bin/uv run pytest              # must pass before Verify
.venv/bin/uv run ruff check && .venv/bin/uv run ruff format --check
```

## Layout

- `src/everyday_news/`: one module per pipeline step:
  fetch → prune → normalize → dedupe → cluster → filters → rank → summarize → digest,
  plus `visits.py` (what's new), `follow.py`, `webview.py`, `cli.py`, and shared pieces:
  `db.py` (schema + `MIGRATIONS`), `sources.py` / `settings.py` (config loaders),
  `keywords.py` (stem matching for muted words and topics).
- User-editable config (TOML): `sources.toml`, `settings.toml`, `filters.toml`, `follow.toml`.
- `news.db` (SQLite) and `digests/` are local data, gitignored.
- `tests/fixtures/`: trimmed real feeds; tests never touch the network.

## Rules

- All project context is Markdown in `context/`. No other doc formats.
- All code work belongs to a change folder in `context/change/NNNN-slug/`
  (`proposal.md`, `plan.md`, `log.md`); numbers are assigned when a change is proposed.
- Stages: Propose → Plan → Build → Verify → Archive.
  Stop after **Propose** and wait for the user's approval. Exceptions: the user approved
  the whole phase, or explicitly told you to build/fix this specific thing now; then
  build it through to Archive. When in doubt, propose and stop.
- Keep `plan.md` checkboxes and `log.md` current while working.
- **Build** ends with pytest and ruff passing (see conventions.md). **Verify** then checks
  the result on the real `news.db` / digest and, if the local `code-reviewer` subagent
  exists (`.claude/agents/`, gitignored, read-only), has it review the changed files:
  give it the change folder and the file list, fix confirmed bugs before archiving.
  If it isn't available, note in `log.md` that the review was skipped.
- When a change is done: update `foundation/` docs it affected, update the roadmap
  status, move the folder to `context/archive/`, add a line to
  `context/archive/README.md`, and make one commit `NNNN: <title>`.
- Open questions and decisions go in `context/foundation/decisions.md`, not in chat only.
- Follow `context/foundation/conventions.md` (schema changes: append to `db.MIGRATIONS`).

## Non-negotiables

- **Polite fetching**: fetch only when the user launches the app, one request per
  source, honest User-Agent, no retries, no redirects, no background or scheduled
  requests. Respect the cooldown; `news fetch --force` only when truly needed, and say so.
- **No LLM, no paid APIs, no secrets.**
- Feed text is untrusted: escape it in Markdown, never render raw HTML in the web view.
- Never put fake data in the real `news.db`; demo on a copy and delete it.
