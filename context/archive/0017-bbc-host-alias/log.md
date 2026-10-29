# 0017 – Log

## 2026-10-29
- User asked to fix the BBC duplicate noticed in 0012. Real DB: article 17 (hn) links
  www.bbc.com/news/articles/cm8xz7pkd0jjo, same id as the BBC feed article.
- `HOST_ALIASES` in `canonical_url`; `recanonicalize()` runs in `news fetch` after normalize,
  before dedupe. Dedupe tie-break "has text" added. Rank borrows a duplicate's discussion link.
- Also added the discussion link to the 📌 line in the Following section.
- Real DB (no requests, cooldown): article 17 (hn) URL → bbc.co.uk, now duplicate of 79 (bbc);
  digest shows the Spain explainer once with the HN discussion link.
- Tests: 132 passed (4 new). Verified and archived.
