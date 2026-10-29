# 0017 – BBC host alias

Stage: Archive · Phase 5

## Why

Hacker News links BBC articles as `www.bbc.com/news/articles/<id>`, the BBC feed uses
`www.bbc.co.uk/news/articles/<id>` for the same article. Exact dedupe (0006) compares
canonical URLs, so it misses them (seen in 0012: the Spain explainer twice).

## What

- `canonical_url` maps host aliases: `bbc.com` / `www.bbc.com` → `www.bbc.co.uk`
  (a small `HOST_ALIASES` table, easy to extend).
- Stored articles are re-canonicalized on every `news fetch` (cheap, idempotent), so the
  existing duplicate is caught without re-fetching.
- Dedupe primary choice gains a tie-break: same weight → prefer the article **with text**
  (else HN's text-less copy, published earlier, would win over BBC's).
- The digest keeps the duplicate's value: a primary without a discussion link borrows
  one from its duplicates (the HN thread shows next to the BBC article), as planned in 0006.

## Acceptance criteria

- Real DB: HN's Spain explainer becomes a duplicate of BBC's; the digest shows the BBC
  article once, with the HN discussion link
- pytest + ruff pass

## Approval

User request (2026-10-29).
