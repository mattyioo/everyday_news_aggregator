"""Command-line entry point: `news fetch`, `news digest`, `news run`, `news sources`,
`news stories`, `news top`."""

from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer

from everyday_news import db
from everyday_news import settings as cfg
from everyday_news.cluster import cluster
from everyday_news.dedupe import mark_duplicates
from everyday_news.digest import DEFAULT_DIR, digest_path, render_digest, write_digest
from everyday_news.fetch import fetch_all, make_client
from everyday_news.filters import FilterConfigError, Filters, apply_filters, load_filters
from everyday_news.normalize import normalize_pending
from everyday_news.prune import prune
from everyday_news.rank import rank_stories
from everyday_news.sources import DEFAULT_PATH, Source, SourceConfigError, load_sources

app = typer.Typer(help="Personal news aggregator.", no_args_is_help=True)

ConfigOption = Annotated[Path, typer.Option("--config", help="Path to sources.toml")]
DbOption = Annotated[Path, typer.Option("--db", help="Path to the SQLite database")]
SettingsOption = Annotated[Path, typer.Option("--settings", help="Path to settings.toml")]
FiltersOption = Annotated[Path, typer.Option("--filters", help="Path to filters.toml")]


def _load(config: Path) -> list[Source]:
    try:
        return load_sources(config)
    except SourceConfigError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(1) from None


def _load_settings(path: Path) -> cfg.Settings:
    try:
        return cfg.load_settings(path)
    except cfg.SettingsError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(1) from None


def _load_filters(path: Path) -> Filters:
    try:
        return load_filters(path)
    except FilterConfigError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def fetch(
    force: Annotated[
        bool, typer.Option("--force", help="Ignore the cooldown (still one request per source)")
    ] = False,
    config: ConfigOption = DEFAULT_PATH,
    settings_path: SettingsOption = cfg.DEFAULT_PATH,
    filters_path: FiltersOption = Path("filters.toml"),
    db_path: DbOption = db.DEFAULT_PATH,
) -> None:
    """Fetch all enabled sources once into the local database, then delete old news."""
    sources = _load(config)
    settings = _load_settings(settings_path)
    filters = _load_filters(filters_path)
    conn = db.connect(db_path)
    try:
        with make_client() as client:
            results = fetch_all(sources, conn, client, force=force)
        deleted = prune(conn, sources, settings.retention_days, datetime.now(UTC))
        added = normalize_pending(conn, sources)
        duplicates = mark_duplicates(conn, sources)
        cluster(conn, sources)
        filtered = apply_filters(conn, filters)
        stories = conn.execute("SELECT COUNT(*) FROM story").fetchone()[0]
    finally:
        conn.close()

    width = max(len(r.source_id) for r in results)
    for r in results:
        typer.echo(f"{r.source_id:<{width}}  {r.status:<7}  {r.detail}")
    requests = sum(r.requested for r in results)
    typer.echo(
        f"{requests} request(s) sent, {added} new article(s), {duplicates} duplicate(s), "
        f"{deleted} deleted (older than {settings.retention_days} days), {stories} stories, "
        f"{filtered} filtered"
    )


OutOption = Annotated[Path, typer.Option("--out", help="Directory for digest files")]


@app.command()
def digest(
    config: ConfigOption = DEFAULT_PATH,
    settings_path: SettingsOption = cfg.DEFAULT_PATH,
    db_path: DbOption = db.DEFAULT_PATH,
    out: OutOption = DEFAULT_DIR,
) -> None:
    """Write today's Markdown digest from stored stories (no network)."""
    sources = _load(config)
    settings = _load_settings(settings_path)
    now = datetime.now(UTC)
    conn = db.connect(db_path)
    try:
        ranking = rank_stories(conn, sources, now, settings.digest_hours)
    finally:
        conn.close()

    path = digest_path(now, out)
    write_digest(render_digest(ranking, sources, settings, now), path)
    typer.echo(f"digest: {path} ({len(ranking.stories)} stories)")


@app.command()
def run(
    config: ConfigOption = DEFAULT_PATH,
    settings_path: SettingsOption = cfg.DEFAULT_PATH,
    filters_path: FiltersOption = Path("filters.toml"),
    db_path: DbOption = db.DEFAULT_PATH,
    out: OutOption = DEFAULT_DIR,
) -> None:
    """Run the full pipeline: fetch once, then write today's digest."""
    fetch(
        force=False,
        config=config,
        settings_path=settings_path,
        filters_path=filters_path,
        db_path=db_path,
    )
    digest(config=config, settings_path=settings_path, db_path=db_path, out=out)


@app.command()
def sources(config: ConfigOption = DEFAULT_PATH) -> None:
    """List configured news sources."""
    for s in _load(config):
        state = "on " if s.enabled else "off"
        typer.echo(f"[{state}] {s.id:<18} {s.lang}  w={s.weight:<4} {s.name}  {s.url}")


@app.command()
def stories(db_path: DbOption = db.DEFAULT_PATH) -> None:
    """List stories covered by more than one article (no network)."""
    conn = db.connect(db_path)
    try:
        rows = conn.execute(
            """
            SELECT story.id, story.lang, story.title, story.last_updated,
                   article.source_id, article.title AS article_title
            FROM story
            JOIN story_article ON story_article.story_id = story.id
            JOIN article ON article.id = story_article.article_id
            WHERE story.id IN (
                SELECT story_id FROM story_article GROUP BY story_id HAVING COUNT(*) > 1
            )
            ORDER BY story.last_updated DESC, story.id, article.published_at
            """
        ).fetchall()
    finally:
        conn.close()

    if not rows:
        typer.echo("no stories with more than one article")
    current = None
    for r in rows:
        if r["id"] != current:
            current = r["id"]
            typer.echo(f"\n[{r['lang']}] {r['title']}  (updated {r['last_updated'][:16]})")
        typer.echo(f"    {r['source_id']:<12} {r['article_title']}")


@app.command()
def top(
    limit: Annotated[int, typer.Option(help="How many stories to show")] = 20,
    config: ConfigOption = DEFAULT_PATH,
    settings_path: SettingsOption = cfg.DEFAULT_PATH,
    db_path: DbOption = db.DEFAULT_PATH,
) -> None:
    """Show the ranked stories of the digest window with score parts (no network)."""
    sources = _load(config)
    settings = _load_settings(settings_path)
    conn = db.connect(db_path)
    try:
        ranking = rank_stories(conn, sources, datetime.now(UTC), settings.digest_hours)
    finally:
        conn.close()

    typer.echo(f"{len(ranking.stories)} stories in the last {settings.digest_hours} h")
    for n, s in enumerate(ranking.stories[:limit], start=1):
        note = f"  [downranked: {s.downranked}]" if s.downranked else ""
        typer.echo(
            f"{n:>3}. {s.score:.2f} (w {s.weight:.1f} × r {s.recency:.2f} × c {s.coverage:.2f})"
            f"  {s.lead.source_id:<11} {s.lead.title}{note}"
        )
