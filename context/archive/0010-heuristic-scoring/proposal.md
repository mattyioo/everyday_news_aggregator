# 0010 – Heuristic scoring

Stage: Archive · Phase 2

## Why

The digest must stay readable in under 10 minutes, so stories need an order: what
matters most first, noise last or gone.

## What

- `src/everyday_news/rank.py`, computed on demand (no new tables):
  `rank_stories(conn, sources, now, hours) -> Ranking` with
  - `stories`: stories that have at least one kept article published in the last
    `hours` (new setting `digest_hours = 24`), best first
  - `dropped`: articles in the same window that filters dropped (for the filtered report, 0013)
- Per story, only kept articles count (dropped ones are hidden; a story whose articles
  are all dropped disappears).
- **Lead article** (what the digest shows and which site section it goes in):
  not downranked > highest source weight > has summary text > earliest.
  This also fixes 0007's cosmetic issue: a "Watch: …" video is never the lead when the
  story has a normal article.
- **Score** = weight × recency × coverage × downrank
  - weight: highest source weight among kept articles
  - recency: halves every 24 h since the story's newest kept article
  - coverage: 1 + 0.5 per extra site + 0.25 per extra article from the same site
  - downrank: × 0.5 when every kept article is downranked (reason kept for display)
- `news top [--limit N]`: ranked stories with score parts (debug aid, no network).

## Acceptance criteria

- Multi-site, fresh stories outrank single-article ones of the same age; Spain crash
  (BBC + HN, 4 articles) is #1 on the real data window
- A fully downranked story scores half; a story with any normal article is not penalised
  and leads with that article
- Stories outside the window and fully dropped stories are excluded
- pytest + ruff pass

## Approval

Part of the Phase 2 + 3 go-ahead (2026-10-29).
