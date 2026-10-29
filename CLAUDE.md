# everyday_news

Personal news aggregator: collects articles from chosen sources, filters out
noise, merges duplicates, and produces a short daily digest.

## Start here

1. Read `context/README.md` for how the workflow works.
2. Read `context/foundation/roadmap.md` to see the current phase.
3. Open the active change in `context/change/` and continue from its stage.

## Rules

- All project context is Markdown in `context/`. No other doc formats.
- All code work belongs to a change folder in `context/change/NNNN-slug/`.
- Stages: Propose → Plan → Build → Verify → Archive.
  Stop after **Propose** and wait for the user's approval before building.
- Keep `plan.md` checkboxes and `log.md` current while working.
- When a change is done: update `foundation/` docs it affected, update the
  roadmap status, move the folder to `context/archive/`, add a line to
  `context/archive/README.md`.
- Open questions go in `context/foundation/decisions.md`, not in chat only.
- Follow `context/foundation/conventions.md`.
