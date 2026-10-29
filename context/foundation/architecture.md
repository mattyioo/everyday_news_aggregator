# Architecture

A pipeline of small, separate steps. Each step reads from and writes to a local
SQLite database, so any step can be re-run on its own.

```
sources.toml ──► Fetch ──► Normalize ──► Dedupe/Cluster ──► Filter/Score ──► Summarize ──► Digest
                  │            │               │                  │               │            │
                  └────────────┴───────────────┴──── SQLite ──────┴───────────────┘            ▼
                                                                                    digests/YYYY-MM-DD.md
```

## Components

| Component | Responsibility |
|---|---|
| **Sources** | User-edited config listing feeds (RSS/Atom), with language, tags, weight and a `fetch_fulltext` flag |
| **Fetch** | Runs once per app launch, never in the background. One request per enabled feed, sequential, honest User-Agent, conditional GET (ETag / Last-Modified), timeouts, no retry loops, 15 min cooldown per source (60 min after a failure), skip a source for the run on 429/5xx/timeout, never follow redirects. Stores raw items |
| **Normalize** | Turn raw items into one `Article` shape (title, url, source, lang, published, text) |
| **Dedupe/Cluster** | Mark exact duplicates (same canonical URL, or same title hash + lang) and keep the highest-weight source as primary; group articles about the same event into a `Story` (shared key words in titles, or overlapping lead text; same language; rolling 3-day window; story ids stable) |
| **Filter/Score** | Rule-based only: muted topics, per-language clickbait patterns, heuristic score (source weight, recency, number of sources covering it). Every decision records a reason |
| **Summarize** | Extractive, no LLM: feed description, or the first sentences of the article text |
| **Digest** | Render the day's top stories to Markdown, one section per site (no topic categories) |
| **Prune** | At launch, delete articles not seen in their feed for `retention_days` (7) |
| **Tracking** *(Phase 4)* | Followed topics; show what is new since the last digest |
| **CLI** | Entry point: `news fetch`, `news digest`, `news run` (everything) |

## Data model

Sources live in `sources.toml` (id, name, url, lang, weight, tags, enabled,
fetch_fulltext), not in the database. Database: `news.db` (SQLite, gitignored).

Built (Phase 1):

- `fetch_state` – source_id, last_fetched_at, last_status, etag, last_modified
- `raw_item` – id, source_id, guid, url, title, summary (HTML), comments_url, published, fetched_at, last_seen_at (retention); unique (source_id, guid)
- `article` – id, raw_item_id (unique), source_id, lang, url (canonical, tracking params removed), discussion_url (HN / Reddit thread), title, text (plain), published_at (UTC ISO), title_hash, duplicate_of (Phase 2: NULL = shown; else the primary article's id)

Schema changes to an existing `news.db` go through `MIGRATIONS` in `db.py` (tracked by `PRAGMA user_version`); never edit a committed migration.

- `story` – id, lang, title (from the highest-weight source), first_seen, last_updated
- `story_article` – story_id, article_id (unique); only primary (non-duplicate) articles

Planned:

- `verdict` – article_id or story_id, kept (bool), score, reason

## Boundaries

- No step talks to another step directly; they share the database.
- No LLM and no paid APIs. Everything runs offline once the feeds are fetched.
- Polish and English stories are clustered separately; the digest has one section per language.
