from pathlib import Path

import pytest
from typer.testing import CliRunner

from everyday_news.cli import app
from everyday_news.sources import SourceConfigError, load_sources

PROJECT_SOURCES = Path(__file__).parent.parent / "sources.toml"

VALID = """
[[source]]
id = "a"
name = "Source A"
url = "https://a.example/rss"
lang = "en"
tags = ["tech"]

[[source]]
id = "b"
name = "Source B"
url = "https://b.example/feed"
lang = "pl"
weight = 0.5
enabled = false
"""


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "sources.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_loads_valid_config_with_defaults(tmp_path: Path) -> None:
    a, b = load_sources(write(tmp_path, VALID))
    assert (a.id, a.lang, a.weight, a.tags, a.enabled, a.fetch_fulltext) == (
        "a", "en", 1.0, ("tech",), True, False,
    )  # fmt: skip
    assert (b.lang, b.weight, b.enabled) == ("pl", 0.5, False)


def test_project_sources_file_is_valid() -> None:
    loaded = load_sources(PROJECT_SOURCES)
    assert {s.id for s in loaded} == {"hn", "reddit-technology", "wp", "znosnenewsy"}
    assert not any(s.fetch_fulltext for s in loaded)


def test_missing_url_is_reported(tmp_path: Path) -> None:
    path = write(tmp_path, '[[source]]\nid = "x"\nname = "X"\nlang = "en"\n')
    with pytest.raises(SourceConfigError, match="source #1: missing or empty 'url'"):
        load_sources(path)


def test_bad_lang_is_reported(tmp_path: Path) -> None:
    path = write(tmp_path, VALID.replace('lang = "pl"', 'lang = "de"'))
    with pytest.raises(SourceConfigError, match="source 'b': lang must be one of"):
        load_sources(path)


def test_duplicate_id_is_reported(tmp_path: Path) -> None:
    path = write(tmp_path, VALID.replace('id = "b"', 'id = "a"'))
    with pytest.raises(SourceConfigError, match="duplicate source id 'a'"):
        load_sources(path)


def test_missing_file_is_reported(tmp_path: Path) -> None:
    with pytest.raises(SourceConfigError, match="file not found"):
        load_sources(tmp_path / "nope.toml")


def test_cli_lists_sources_and_reports_errors(tmp_path: Path) -> None:
    runner = CliRunner()
    ok = runner.invoke(app, ["sources", "--config", str(write(tmp_path, VALID))])
    assert ok.exit_code == 0
    assert "[on ] a" in ok.output
    assert "[off] b" in ok.output

    bad = runner.invoke(app, ["sources", "--config", str(tmp_path / "nope.toml")])
    assert bad.exit_code == 1
    assert "file not found" in bad.output
