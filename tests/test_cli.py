from pathlib import Path

from typer.testing import CliRunner

from everyday_news.cli import app

runner = CliRunner()


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
    result = runner.invoke(app, ["run", "--config", str(config), "--db", str(tmp_path / "news.db")])
    assert result.exit_code == 0, result.output
    assert "x  skipped  disabled" in result.output
    assert "0 request(s) sent, 0 new article(s)" in result.output
    assert "digest:" in result.output
