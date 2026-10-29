# 0007 – Story clustering

Stage: Archive · Phase 2

## Why

Exact dedupe (0006) catches identical URLs/titles. Same-event coverage with different
headlines still shows up several times. Real `news.db` today (85 primaries):

| Event | Articles | Difficulty |
|---|---|---|
| Spain train crash | hn 1 + bbc 3 | different headlines, shared key words |
| Thomas Markle police search | bbc 2 | shared names |
| iPhone Duo folding test | znosnenewsy 2 | Polish inflection ("iPhona"), mixed EN/PL words |
| S19 viaduct (estakada) video | wp 2 | headlines share nothing; only lead text overlaps |

False-positive trap seen: HN "Toxic Experts" vs a BBC story. HN items have no text,
so overlap measured against a tiny word set looks high.

## What

- `story` table (id, lang, title, first_seen, last_updated) and `story_article`
  (story_id, article_id unique), migration 3. Only primary articles (`duplicate_of IS NULL`)
  are clustered; an article that later becomes a duplicate leaves its story, and stories
  left empty (e.g. after retention deletes their articles) are deleted.
- **Incremental, stable ids**: each new article joins the best-matching existing story
  in its language whose newest article is within 3 days (rolling window, so slow sites
  like znosnenewsy still group), otherwise starts a new story.
  Existing assignments are never reshuffled (Phase 4 tracking needs stable story ids).
- Similarity, stdlib only (no `rapidfuzz` needed after all):
  - "key words": casefolded words ≥ 3 characters (keeps "duo", "s19"), minus EN/PL stopword lists,
    cut to a 5-letter prefix (cheap stemming: `iphona`/`iphone` → `iphon`, `pociągu`/`pociąg` → `pocią`)
  - title score: Jaccard of title key words
  - text score: overlap of title+lead key words, only when **both** sides have ≥ 8 key words
    (kills the empty-HN-text false positive)
  - match if title ≥ 0.3 or text ≥ 0.4; thresholds tuned on the real data and pinned by tests
- Story title: title of the article from the highest-weight source (earliest on ties).
- `src/everyday_news/cluster.py`, runs in `news fetch` after dedupe; summary line gains `, N story(ies)`.
- `news stories` command: list multi-article stories (debug aid until the digest exists).
- Digest context (decided after this proposal): the digest is grouped by site, so a
  story spanning sites will appear once, under its highest-weight site, "also on …".

## Out of scope

Cross-language grouping (decided: EN and PL stay separate). Ranking, filtering.

## Acceptance criteria

- On test data built from the real titles/leads above: Spain crash = 1 story of 4,
  Markle = 1 of 2, iPhone Duo Oct 25 + 26 = 1 story (Oct 20 announcement, 5 days
  earlier, stays separate), S19 = 1 of 2; "Toxic Experts" stays alone
- No story mixes languages; articles > 3 days after a story's newest article start a new one
- Re-running assigns nothing new; story ids unchanged
- pytest + ruff pass

## Approval

Approved by the user on 2026-10-29.
