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
| **Fetch** | Runs once per app launch, never in the background. One request per enabled feed, sequential, honest User-Agent, conditional GET (ETag / Last-Modified), timeouts, no retry loops, skip a source for the run on 429/5xx. Stores raw items |
| **Normalize** | Turn raw items into one `Article` shape (title, url, source, lang, published, text) |
| **Dedupe/Cluster** | Drop exact duplicates (URL/hash); group articles about the same event into a `Story` by fuzzy title match, within one language |
| **Filter/Score** | Rule-based only: muted topics, per-language clickbait patterns, heuristic score (source weight, recency, number of sources covering it, HN points / Reddit score). Every decision records a reason |
| **Summarize** | Extractive, no LLM: feed description, or the first sentences of the article text |
| **Digest** | Render the day's top stories to Markdown (later: HTML / web view) |
| **Tracking** *(Phase 4)* | Followed topics; show what is new since the last digest |
| **CLI** | Entry point: `news fetch`, `news digest`, `news run` (everything) |

## Data model (initial)

- `source` – id, name, url, lang, tags, weight, fetch_fulltext, enabled
- `article` – id, source_id, url, title, lang, published_at, text, content_hash, fetched_at
- `story` – id, title, first_seen, last_updated
- `story_article` – story_id, article_id
- `verdict` – article_id or story_id, kept (bool), score, reason

## Boundaries

- No step talks to another step directly; they share the database.
- No LLM and no paid APIs. Everything runs offline once the feeds are fetched.
- Polish and English stories are clustered separately; the digest has one section per language.
