from typer.testing import CliRunner

from everyday_news.cli import app

runner = CliRunner()


def test_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for command in ("fetch", "digest", "run"):
        assert command in result.output


def test_run_calls_fetch_and_digest() -> None:
    result = runner.invoke(app, ["run"])
    assert result.exit_code == 0
    assert "fetch:" in result.output
    assert "digest:" in result.output
