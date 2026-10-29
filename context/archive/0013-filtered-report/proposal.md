# 0013 – Filtered report

Stage: Archive · Phase 3

## Why

Vision principle: "Transparent filtering. Every dropped item has a stated reason I can
inspect." Hidden articles must be one glance away, so a wrong rule is easy to spot.

## What

- Last digest section `## Filtered out (N)`:
  - one line pointing at `filters.toml` for tuning
  - dropped articles from the digest window grouped by reason (most common first),
    each with link, site and time
  - a one-line tally of downranked articles by reason (they are still in the digest,
    lower down): e.g. `Downranked but shown: teaser headline 6 · video 3 · promotion 1`
  - nothing filtered → "_Nothing was filtered out._"
- Data comes from `Ranking.dropped` (0010) and the verdicts on ranked stories' items.

## Acceptance criteria

- Real digest lists "Aż 1,5 mln wyświetleń…" under "clickbait: view-count bait" with link,
  and the downrank tally matches the stored verdicts in the window
- pytest + ruff pass

## Approval

Part of the Phase 2 + 3 go-ahead (2026-10-29).
