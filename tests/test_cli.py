from pathlib import Path

from typer.testing import CliRunner

from everyday_news.cli import app

runner = CliRunner()
ROOT = Path(__file__).parent.parent


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("fetch", "digest", "run", "sources"):
        assert command in result.output


def test_run_calls_fetch_and_digest(tmp_path: Path) -> None:
    # A disabled source keeps this test off the network.
    config = tmp_path / "sources.toml"
    config.write_text(
        '[[source]]\nid = "x"\nname = "X"\nurl = "https://x.example/rss"\n'
        'lang = "en"\nenabled = false\n',
        encoding="utf-8",
    )
    settings = tmp_path / "settings.toml"
    settings.write_text("retention_days = 30\n", encoding="utf-8")
    result = runner.invoke(
        app,
        [
            "run",
            "--config",
            str(config),
            "--settings",
            str(settings),
            "--filters",
            str(ROOT / "filters.toml"),
            "--db",
            str(tmp_path / "x.db"),
        ],
    )
    assert result.exit_code == 0, result.output
    assert "x  skipped  disabled" in result.output
    assert "0 request(s) sent, 0 new article(s), 0 duplicate(s), 0 deleted" in result.output
    assert "0 stories, 0 filtered" in result.output
    assert "digest:" in result.output
