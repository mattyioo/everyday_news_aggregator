"""Command-line entry point: `news fetch`, `news digest`, `news run`, `news sources`."""

from pathlib import Path
from typing import Annotated

import typer

from everyday_news import db
from everyday_news.dedupe import mark_duplicates
from everyday_news.fetch import fetch_all, make_client
from everyday_news.normalize import normalize_pending
from everyday_news.sources import DEFAULT_PATH, Source, SourceConfigError, load_sources

app = typer.Typer(help="Personal news aggregator.", no_args_is_help=True)

ConfigOption = Annotated[Path, typer.Option("--config", help="Path to sources.toml")]
DbOption = Annotated[Path, typer.Option("--db", help="Path to the SQLite database")]


def _load(config: Path) -> list[Source]:
    try:
        return load_sources(config)
    except SourceConfigError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(1) from None


@app.command()
def fetch(
    force: Annotated[
        bool, typer.Option("--force", help="Ignore the cooldown (still one request per source)")
    ] = False,
    config: ConfigOption = DEFAULT_PATH,
    db_path: DbOption = db.DEFAULT_PATH,
) -> None:
    """Fetch all enabled sources once into the local database."""
    sources = _load(config)
    conn = db.connect(db_path)
    try:
        with make_client() as client:
            results = fetch_all(sources, conn, client, force=force)
        added = normalize_pending(conn, sources)
        duplicates = mark_duplicates(conn, sources)
    finally:
        conn.close()

    width = max(len(r.source_id) for r in results)
    for r in results:
        typer.echo(f"{r.source_id:<{width}}  {r.status:<7}  {r.detail}")
    requests = sum(r.requested for r in results)
    typer.echo(f"{requests} request(s) sent, {added} new article(s), {duplicates} duplicate(s)")


@app.command()
def digest() -> None:
    """Build today's Markdown digest from stored stories."""
    typer.echo("digest: not implemented yet (change 0010)")


@app.command()
def run(config: ConfigOption = DEFAULT_PATH, db_path: DbOption = db.DEFAULT_PATH) -> None:
    """Run the full pipeline: fetch, then digest."""
    fetch(force=False, config=config, db_path=db_path)
    digest()


@app.command()
def sources(config: ConfigOption = DEFAULT_PATH) -> None:
    """List configured news sources."""
    for s in _load(config):
        state = "on " if s.enabled else "off"
        typer.echo(f"[{state}] {s.id:<18} {s.lang}  w={s.weight:<4} {s.name}  {s.url}")
