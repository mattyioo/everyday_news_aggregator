# 0015 – What's new

Stage: Archive · Phase 4

## Why

The app is opened several times a day (one refresh per launch). Rereading the same
stories each time is exactly the noise the app should remove.

## What

- Migration 5: `digest_run` (id, generated_at). `news digest` / `news run` record a row
  after writing the file.
- **Baseline** = the last digest written *before the most recent fetch*
  (`MAX(fetch_state.last_fetched_at)`). So:
  - `news run` → fetch, then digest: new = fetched since the previous visit's digest
  - rerunning `news digest`, or relaunching inside the 15-min cooldown (no new fetch),
    keeps the same markers instead of wiping them
  - no earlier digest → first digest, no markers
- "New" uses the time the app **fetched** an article (`raw_item.fetched_at`), not the
  publish date, so backdated items still count as new to the reader.
- Per story: **new** (every kept article arrived after the baseline), **updated** (some
  did, some were seen before), else seen.
- Digest:
  - header: `N new · M updated since your last digest (D Mon HH:MM)` or "First digest"
  - 🆕 before new stories, 🔄 before updated ones; inside an updated story, the new
    articles are labelled "(new)"
  - within each site section, new and updated stories come first, then seen ones,
    each by score; the per-site cap therefore cuts seen stories first
  - story id in the meta line (`#123`), needed to follow a story (0016)

## Acceptance criteria

- Two real `news run`s: the second digest marks only what arrived in between
- `news digest` twice in a row: same markers
- pytest + ruff pass

## Approval

Part of the Phase 4 go-ahead (2026-10-29).
