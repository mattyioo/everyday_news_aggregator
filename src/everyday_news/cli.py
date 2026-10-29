"""Command-line entry point: `news fetch`, `news digest`, `news run`, `news sources`."""

from pathlib import Path
from typing import Annotated

import typer

from everyday_news.sources import DEFAULT_PATH, SourceConfigError, load_sources

app = typer.Typer(help="Personal news aggregator.", no_args_is_help=True)


@app.command()
def fetch() -> None:
    """Fetch all configured sources into the local database."""
    typer.echo("fetch: not implemented yet (change 0003)")


@app.command()
def digest() -> None:
    """Build today's Markdown digest from stored stories."""
    typer.echo("digest: not implemented yet (change 0010)")


@app.command()
def run() -> None:
    """Run the full pipeline: fetch, then digest."""
    fetch()
    digest()


@app.command()
def sources(
    config: Annotated[Path, typer.Option(help="Path to sources.toml")] = DEFAULT_PATH,
) -> None:
    """List configured news sources."""
    try:
        loaded = load_sources(config)
    except SourceConfigError as e:
        typer.echo(f"error: {e}", err=True)
        raise typer.Exit(1) from None

    for s in loaded:
        state = "on " if s.enabled else "off"
        typer.echo(f"[{state}] {s.id:<18} {s.lang}  w={s.weight:<4} {s.name}  {s.url}")
