from pathlib import Path

import pytest

from everyday_news import db
from everyday_news.filters import (
    FilterConfigError,
    apply_filters,
    evaluate,
    load_filters,
)
from everyday_news.normalize import title_hash

ROOT = Path(__file__).parent.parent


@pytest.fixture(scope="module")
def project_filters():
    return load_filters(ROOT / "filters.toml")


def write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "filters.toml"
    path.write_text(text, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "title, lang, expected",
    [
        ("Aż 1,5 mln wyświetleń. Polska zachwyca się filmem z budowy", "pl",
         ("drop", "clickbait: view-count bait")),
        ("Kaczyński o UE. Burza o ludzi Brauna na RBN [SKRÓT DNIA]", "pl", ("downrank", "roundup")),
        ("Podpalili stację Starlink na Litwie. Jest nagranie", "pl",
         ("downrank", "teaser headline")),
        ("Nowe stanowisko dla Orbána w USA? Ostra reakcja Magyara", "pl",
         ("downrank", "teaser headline")),
        ('"Gra w grę Tuska". Temat polexitu zaszkodzi PiS? Tak oceniają to politycy', "pl",
         ("downrank", "teaser headline")),
        ("Tak werbują rosyjskie służby. Kilka tysięcy złotych za plecak", "pl",
         ("downrank", "teaser headline")),
        ("O czym Trump rozmawiał z AI? Jest żądanie i specjalny list", "pl",
         ("downrank", "teaser headline")),
        ("Watch: At the scene of Spain's deadly train crash", "en", ("downrank", "video")),
        ("Launch HN: Simantic (YC F26) – Firmware Simulation for AI Agents", "en",
         ("downrank", "promotion (YC launch)")),
        ("You won't believe what this cat did", "en", ("drop", "clickbait: sensational phrasing")),
        ("Wypadek śmigłowca EUFOR. Trzy osoby nie żyją", "pl", None),
        ("Sąd uchylił decyzję ws. Ziobry. W tle komisja Pegasusa", "pl", None),
        ("Russian drone attack on Ukrainian train station kills at least 14", "en", None),
        ("How could Israel break election deadlock? Here are four scenarios", "en", None),
        ("Watch: same words, but Polish source", "pl", None),  # rules are per language
    ],
)  # fmt: skip
def test_project_rules_on_real_headlines(project_filters, title, lang, expected) -> None:
    verdict = evaluate(title, "", lang, project_filters)
    assert (verdict.action, verdict.reason) == expected if expected else verdict is None


def test_muted_words_match_stems_and_whole_short_words(tmp_path: Path) -> None:
    filters = load_filters(write(tmp_path, 'muted = ["celebry", "f1"]\n'))
    assert evaluate("Celebryci na gali", "", "pl", filters).reason == "muted: celebry"
    assert evaluate("Results", "F1 race in Monaco", "en", filters).reason == "muted: f1"
    assert evaluate("F150 truck recall", "", "en", filters) is None


def test_drop_beats_downrank(tmp_path: Path) -> None:
    config = """
[[rule]]
lang = "any"
pattern = "^watch:"
action = "downrank"
reason = "video"

[[rule]]
lang = "any"
pattern = "goes viral"
action = "drop"
reason = "viral"
"""
    filters = load_filters(write(tmp_path, config))
    assert evaluate("Watch: dog goes viral", "", "en", filters).reason == "viral"


@pytest.mark.parametrize(
    "config, message",
    [
        ('muted = "x"\n', "muted must be a list"),
        ('muted = ["two words"]\n', "must be a single word"),
        ('[[rule]]\nlang = "de"\npattern = "x"\naction = "drop"\nreason = "r"\n', "lang must be"),
        ('[[rule]]\nlang = "en"\npattern = "x"\naction = "hide"\nreason = "r"\n', "action must"),
        (
            '[[rule]]\nlang = "en"\npattern = "(x"\naction = "drop"\nreason = "r"\n',
            "invalid pattern",
        ),
        ('[[rule]]\nlang = "en"\npattern = "x"\naction = "drop"\n', "missing or empty 'reason'"),
    ],
)
def test_config_errors(tmp_path: Path, config: str, message: str) -> None:
    with pytest.raises(FilterConfigError, match=message):
        load_filters(write(tmp_path, config))


def test_apply_filters_recomputes_all_verdicts(tmp_path: Path) -> None:
    conn = db.connect(tmp_path / "news.db")
    for i, title in enumerate(["Celebrity wedding", "Budget vote"], start=1):
        conn.execute(
            "INSERT INTO article (raw_item_id, source_id, lang, url, title, text, published_at,"
            " title_hash) VALUES (?, 'x', 'en', ?, ?, '', '2026', ?)",
            (i, f"https://x/{i}", title, title_hash(title)),
        )
    assert apply_filters(conn, load_filters(write(tmp_path, 'muted = ["celebrit"]\n'))) == 1
    assert apply_filters(conn, load_filters(write(tmp_path, 'muted = ["budget"]\n'))) == 1
    rows = conn.execute("SELECT article_id, reason FROM article_verdict").fetchall()
    assert [tuple(r) for r in rows] == [(2, "muted: budget")]
    conn.close()
