# 0018 – Web view

Stage: Archive · Phase 5

## Why

Reading the digest as a styled page in the browser is nicer than a raw Markdown file,
and the digest archive (files are kept forever) becomes browsable.

## What

- `news web [--port 8765] [--no-fetch] [--no-open]`: "launching the app" in the browser:
  1. runs `news run` once (fetch with the usual cooldown/politeness, then digest) unless
     `--no-fetch`; no further requests while the page is open (refresh-on-launch rule)
  2. serves a local page on **127.0.0.1 only** and opens it in the default browser
- `src/everyday_news/webview.py`:
  - `/` latest digest, `/d/YYYY-MM-DD` a given day, `/archive` list of all digests
  - prev/next day links; links to articles open in a new tab
  - Markdown → HTML with `markdown-it-py` (CommonMark, **raw HTML disabled**, unsafe link
    schemes like `javascript:` not linked)
  - only paths matching the date pattern are read from `digests/` (no path traversal)
  - one inline stylesheet: readable width, light/dark from the system setting, mobile-friendly
  - routing is a pure function (`route(path, directory)`), the HTTP handler only wraps it
- Stop with Ctrl+C.

## Out of scope

Buttons to follow/unfollow from the page (CLI stays the way to change state).

## Acceptance criteria

- Real: `news web --no-open` serves the latest digest and archive; pages render with
  sections, links, badges; 404 for unknown paths
- Feed text cannot inject HTML/scripts; `../` paths rejected
- pytest + ruff pass

## Approval

User request (2026-10-29).
