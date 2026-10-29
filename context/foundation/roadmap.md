# Roadmap

The project is built in **phases**. Each phase is a set of **changes**
(folders in `context/change/`). Each change goes through the five **stages**
described in `context/README.md`: Propose → Plan → Build → Verify → Archive.

A phase is done when all its changes are archived and its exit criteria hold.

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
| 0002-sources-config – `sources.toml` with HN, r/technology, WP.pl, znosnenewsy.pl (lang, tags, weights) | ✅ archived |
| 0003-feed-fetcher – fetch RSS/Atom once per launch, politely (User-Agent, conditional GET, no retries); store raw items | ✅ archived |
| 0004-normalize-and-store – `Article` model, SQLite schema | ✅ archived |

**Exit:** `news fetch` pulls all configured feeds into SQLite without errors.
_Met for HN, WP.pl and znosnenewsy.pl. Reddit was rate-limited (429) by development test requests on 2026-10-29; recheck on the next normal launch._

## Phase 2 – Noise Removal

Turn a pile of articles into a short list of real stories.

| Change | Status |
|---|---|
| 0005-exact-dedupe – URL / content hash duplicates | ⏳ |
| 0006-story-clustering – group same-event articles into stories (fuzzy titles, per language) | ⏳ |
| 0007-rule-filters – muted topics, EN + PL clickbait patterns, with reasons | ⏳ |
| 0008-heuristic-scoring – rank by source weight, recency, coverage, HN points | ⏳ |

**Exit:** a day's articles reduce to a ranked story list; every drop has a reason.

## Phase 3 – Digest

Something to actually read.

| Change | Status |
|---|---|
| 0009-summaries – extractive per-story summary (feed description / lead sentences) | ⏳ |
| 0010-markdown-digest – `digests/YYYY-MM-DD.md`, English and Polish sections | ⏳ |
| 0011-filtered-report – "what was dropped and why" section | ⏳ |

**Exit:** `news run` produces a digest readable in under 10 minutes.

## Phase 4 – Tracking

Follow stories over days instead of rereading them.

| Change | Status |
|---|---|
| 0012-followed-topics – follow/unfollow topics or stories | ⏳ |
| 0013-whats-new – show only new developments since last digest | ⏳ |

**Exit:** a followed story shows only its updates in later digests.

## Phase 5 – Automation & Polish

Nicer to use.

| Change | Status |
|---|---|
| ~~0014-scheduled-runs~~ – dropped: refresh only on launch (see decisions) | ❌ |
| 0015-feedback-loop – mark items as noise/useful to tune filters | ⏳ |
| 0016-web-view *(optional)* – local page for browsing digests | ⏳ |

**Exit:** one `news run` on launch gives a tuned, readable digest.
