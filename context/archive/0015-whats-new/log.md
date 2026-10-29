# 0015 – Log

## 2026-10-29
- Proposed under the Phase 4 go-ahead. Built before followed-topics: following needs the baseline.
- `visits.py`: `record_digest`, `baseline` (last digest before the latest fetch attempt).
  Rank items now carry `fetched` (join `raw_item`); test helpers updated.
- Empty site text changed from "Nothing new." to "No stories in the window." — "new" now
  means "since your last digest".
- Story id shown as `\#123` in the meta line (escaped so Markdown doesn't treat it as a heading).
- Real check (migration 5): two digests without a fetch → both "First digest"; then
  `news fetch --force` (cooldown still running; one request per site) + digest →
  "2 new · 0 updated since your last digest (19:51)", the two new HN posts on top with 🆕;
  rewriting the digest again kept the same line.
- Tests: 117 passed (4 new). Verified and archived.
