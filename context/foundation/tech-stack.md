# Tech Stack

| Area | Choice | Why |
|---|---|---|
| Language | Python 3.12+ (3.14 installed locally) | Best library support for feeds and text processing |
| Environment | `python -m venv .venv`, then `pip install uv` inside it | No system-wide installs (decision Q6) |
| Packaging | `uv` (from `.venv`) + `pyproject.toml` | Fast dependency management and lockfile |
| Feed parsing | `feedparser` | De facto standard for RSS/Atom |
| HTTP | `httpx` | Timeouts, redirects, custom User-Agent |
| Article text | `trafilatura` | Extracts main text from article pages |
| Storage | SQLite (stdlib `sqlite3`) | Local, zero setup, easy to inspect |
| Config | `sources.toml` (stdlib `tomllib`) | Human-editable |
| CLI | `typer` | Simple commands with help text |
| Similarity | `rapidfuzz` | Fast fuzzy title matching for clustering, no ML |
| LLM | **none** | Decision Q2 |
| Tests | `pytest` | Standard |
| Lint/format | `ruff` | One tool for both |
| Output | Markdown digest files | Decision Q3 |
| Scheduling | systemd user timer or cron *(Phase 5)* | Daily run without manual steps |

## Sources

All checked working on 2026-10-29.

| Source | Lang | Feed | Notes |
|---|---|---|---|
| Hacker News | en | `https://news.ycombinator.com/rss` | Front page only. `hnrss.org/frontpage` adds points and comment counts, useful for scoring later |
| Reddit r/technology | en | `https://www.reddit.com/r/technology/.rss` | Atom feed. Needs a descriptive User-Agent; returns 429 on rapid repeat requests, so fetch once per run. Items link to external articles |
| WP.pl – Wiadomości | pl | `https://wiadomosci.wp.pl/rss.xml` | High volume, more clickbait: main target for noise filters |
| Znośne Newsy | pl | `https://znosnenewsy.pl/feed` | Low volume, curated |
