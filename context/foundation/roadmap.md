# Roadmap

The project is built in **phases**. Each phase is a set of **changes**
(folders in `context/change/`). Each change goes through the five **stages**
described in `context/README.md`: Propose → Plan → Build → Verify → Archive.

A phase is done when all its changes are archived and its exit criteria hold.

Planned changes have no number yet; a number is assigned when the change is proposed
(next free number), so inserting work never renumbers the plan.

Status: ✅ done · 🔄 in progress · ⏳ not started · ❌ dropped

---

## Phase 0 – Foundation ✅

Set up the context system and agree on the vision.

| Change | Status |
|---|---|
| 0000-context-system | ✅ archived |

**Exit:** context folders exist, vision/architecture/roadmap written.

## Phase 1 – Ingestion ✅

Get articles from my sources into a local database.

| Change | Status |
|---|---|
| 0001-project-skeleton – package, CLI stub, tooling, tests running | ✅ archived |
| 0002-sources-config – `sources.toml` with HN, r/technology (later BBC), WP.pl, znosnenewsy.pl (lang, tags, weights) | ✅ archived |
| 0003-feed-fetcher – fetch RSS/Atom once per launch, politely (User-Agent, conditional GET, no retries); store raw items | ✅ archived |
| 0004-normalize-and-store – `Article` model, SQLite schema | ✅ archived |
| 0005-replace-reddit-with-bbc – Reddit rate-limited, swapped for BBC News World | ✅ archived |

**Exit:** `news fetch` pulls all configured feeds into SQLite without errors.
_Met 2026-10-29 for HN, BBC, WP.pl, znosnenewsy.pl. Reddit could not meet it (rate-limited) and was replaced in 0005._

## Phase 2 – Noise Removal ✅

Turn a pile of articles into a short list of real stories.

| Change | Status |
|---|---|
| 0006-exact-dedupe – same canonical URL or same title hash | ✅ archived |
| 0007-story-clustering – group same-event articles into stories (fuzzy titles, per language) | ✅ archived |
| 0008-retention – delete articles 30 days after they leave their feed | ✅ archived |
| 0009-rule-filters – muted topics, EN + PL clickbait patterns, with reasons | ✅ archived |
| 0010-heuristic-scoring – rank by source weight, recency, coverage | ✅ archived |

**Exit:** a day's articles reduce to a ranked story list; every drop has a reason.

## Phase 3 – Digest

Something to actually read.

| Change | Status |
|---|---|
| summaries – extractive per-story summary (feed description / lead sentences) | ⏳ |
| markdown-digest – `digests/YYYY-MM-DD.md`, one section per site | ⏳ |
| filtered-report – "what was dropped and why" section | ⏳ |

**Exit:** `news run` produces a digest readable in under 10 minutes.

## Phase 4 – Tracking

Follow stories over days instead of rereading them.

| Change | Status |
|---|---|
| followed-topics – follow/unfollow topics or stories | ⏳ |
| whats-new – show only new developments since last digest | ⏳ |

**Exit:** a followed story shows only its updates in later digests.

## Phase 5 – Automation & Polish

Nicer to use.

| Change | Status |
|---|---|
| ~~scheduled-runs~~ – dropped: refresh only on launch (see decisions) | ❌ |
| feedback-loop – mark items as noise/useful to tune filters | ⏳ |
| web-view *(optional)* – local page for browsing digests | ⏳ |

**Exit:** one `news run` on launch gives a tuned, readable digest.
