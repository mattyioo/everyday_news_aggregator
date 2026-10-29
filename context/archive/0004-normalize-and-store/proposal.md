# 0004 – Normalize and store

Stage: Archive · Phase 1

## Why

Each feed puts different things in its fields (HN: only a "Comments" link; Reddit:
"submitted by" boilerplate with the real article behind `[link]`; WP: an image plus
lead; Znośne Newsy: a "[…]" and a "pochodzi z serwisu" footer). Later steps (dedupe,
filters, digest) need one clean shape.

## What

- `src/everyday_news/normalize.py` with an `Article` dataclass:
  `source_id, lang, url, discussion_url, title, text, published_at, title_hash`
- Rules (feed-shape based, not hard-coded per source id):
  - `url`: the article itself. Reddit-style `[link]` in the summary wins over the item link.
    Tracking params (`utm_*`, `fbclid`, `gclid`, `mc_cid`, `mc_eid`, `ref_src`) removed, host lowercased
  - `discussion_url`: HN `comments` link, or the Reddit post when the article is external
  - `text`: summary as plain text; images dropped; Reddit boilerplate, WordPress
    "Artykuł … pochodzi z serwisu …" / "The post … appeared first on …" footers and `[…]` removed;
    a bare "Comments" becomes empty
  - `published_at`: UTC ISO; falls back to fetch time
  - `title_hash`: sha256 of the title casefolded, punctuation stripped, whitespace collapsed (for 0005 dedupe)
  - `lang`: from the source config
- `article` table, one row per raw item (`raw_item_id` unique); normalization is idempotent
- `news fetch` normalizes new raw items after fetching (no extra requests) and reports the count

## Out of scope

Dedupe, clustering, scoring. Full-text fetching.

## Acceptance criteria

- Every stored raw item from the four sources becomes one article with a non-empty title and `https` url
- Reddit articles point at the external site; HN/Reddit keep a discussion link
- No HTML tags or entities left in `title` / `text`
- Running normalize twice adds nothing
- Tests on the four real fixtures; pytest + ruff pass

## Approval

Approved by the user as part of "work until Phase 1 is complete" (2026-10-29).
