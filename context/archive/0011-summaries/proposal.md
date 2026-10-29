# 0011 – Summaries

Stage: Archive · Phase 3

## Why

Each digest entry needs one or two lines saying what happened, without an LLM and
without fetching article pages (no extra requests).

## What

- `src/everyday_news/summarize.py`, extractive:
  - `summarize(text, max_chars=280)`: whole sentences from the start of the text while they
    fit; a first sentence longer than the cap is cut at a word boundary with "…"
  - text that ends mid-sentence (znosnenewsy excerpts: "… Właśnie") is trimmed back to the
    last full sentence, or gets "…" if there is none
  - sentence splitting knows common EN/PL abbreviations (`U.S.`, `ws.`, `m.in.`, `np.`,
    `tys.`, `mln`, `dr`, `prof.`, single initials) so it does not cut after them
  - `story_summary(story)`: summary of the first item with text (lead first), else `""`
    (HN-only stories: the digest shows the link and discussion instead)
- Real data (lead text length): BBC avg 112 chars, WP avg 304 (max 438), znosnenewsy
  avg 131 (often truncated mid-sentence), HN always empty.

## Acceptance criteria

- WP 3-sentence leads over 280 chars → first sentences that fit; BBC leads unchanged;
  znosnenewsy truncated excerpts end at a full sentence
- No cut after "U.S." / "ws." / "m.in."
- pytest + ruff pass

## Approval

Part of the Phase 2 + 3 go-ahead (2026-10-29).
