"""Command-line entry point: `news fetch`, `news digest`, `news run`."""

import typer

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
