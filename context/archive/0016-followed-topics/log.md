# 0016 – Log

## 2026-10-29
- Proposed under the Phase 4 go-ahead. No topics given by the user: `follow.toml` starts empty.
- `keywords.py` extracted from filters (muted words) and reused for topics; filter tests
  unchanged and green.
- `rank.stories_by_id` (no window) via a shared `_load_items`.
- Cluster: followed stories accept new articles up to 30 days after their newest one;
  dangling follows removed. Prune: followed stories' articles are never deleted.
- Digest: "Following" section first (📌 story → only articles fetched since the last
  digest; topics → new/updated matches); shown stories skipped in site sections.
- `news follow` / `following` print the digest's lead headline, not `story.title`
  (which can be a "Watch:" video, see 0007 log).
- Real: followed #15 (Spain crash) → Following shows it, "no updates since your last
  digest", not repeated under BBC. Exit demo on a DB copy with one synthetic update:
  only that update listed under the story. Copy deleted.
- Tests: 128 passed (11 new). Verified and archived.
