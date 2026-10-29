# 0016 – Followed stories and topics

Stage: Archive · Phase 4

## Why

Some events run for days (an election, a crash investigation). The reader wants to
keep an eye on them without rereading everything: only the updates.

## What

- **Follow a story** by the id shown in the digest (`\#123`) or `news top` / `news stories`:
  `news follow 123`, `news unfollow 123`, `news following` (list). Stored in the DB
  (migration 6: `followed_story`), since story ids live there.
- **Follow a topic** with words in a new `follow.toml` (`topics = []`, empty by default),
  same stem matching as muted words (shared helper `keywords.py`, also used by filters).
- Digest gets a **"Following"** section at the top (only when something is followed):
  - each followed story: its title and id, then **only the articles that arrived since the
    last digest**; none → "_no updates since your last digest_". Not limited by the
    digest window: a followed story can be days old.
  - each topic: stories in the digest window matching the word that are new or updated
    since the last digest (all matches on the first digest).
  - Stories shown under Following are left out of the site sections (no repeats).
- **Followed stories keep growing**: clustering lets a new article join a followed story
  up to 30 days after its newest article (3 days for others), so a story that goes quiet
  for a few days isn't split and lost.
- **Retention exemption**: articles of followed stories are not deleted (as promised in
  0008). Unfollowing makes them normal again.
- Followed rows of stories that no longer exist are removed during clustering.

## Acceptance criteria (Phase 4 exit)

- A followed story shows only its updates in later digests
- `news follow` on an unknown id → clear error, exit 1
- Topic matches appear under Following, not twice
- Followed stories' articles survive retention
- pytest + ruff pass

## Approval

Part of the Phase 4 go-ahead (2026-10-29).
