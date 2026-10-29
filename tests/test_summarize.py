from datetime import UTC, datetime

import pytest

from everyday_news.rank import Item, RankedStory
from everyday_news.summarize import sentences, story_summary, summarize

# Real leads from news.db, 2026-10-29
WP_TRUMP = (
    "Prezydent USA Donald Trump oświadczył, że na prośbę Luli da Silvy nie opowiedział się po "
    'żadnej ze stron w brazylijskich wyborach. Jednocześnie nazwał głosowanie "hańbą" i '
    "odmówił wskazania prawowitego zwycięzcy. W tym samym czasie pokonany kandydat Flávio "
    "Bolsonaro zbiegł do Stanów Zjednoczonych."
)
BBC_TAPES = (
    "The leaked tapes appear to show one high-speed train was given clearance to move at normal "
    "speed, even though another up ahead had stalled."
)
ZN_RETRO = (
    "W poszukiwaniu analogowych wrażeń coraz częściej sięgamy do przeszłości – my użytkownicy, "
    "a więc marki sprytnie muszą to wykorzystywać. Właśnie"
)
ZN_APKI = (
    "Potencjał ekranowy oczywiście, bo chodzi tu o wymiary i o kodowanie aplikacji, aby do "
    "tego ekranu pasowały. TechCrunch przygotował ciekawe"
)


def test_long_lead_keeps_whole_sentences_that_fit() -> None:
    assert len(WP_TRUMP) > 280
    summary = summarize(WP_TRUMP)
    assert summary.endswith("odmówił wskazania prawowitego zwycięzcy.")
    assert len(summary) <= 280


def test_short_lead_unchanged() -> None:
    assert summarize(BBC_TAPES) == BBC_TAPES


def test_truncated_excerpt_ends_at_last_full_sentence() -> None:
    assert summarize(ZN_RETRO).endswith("muszą to wykorzystywać.")
    assert summarize(ZN_APKI).endswith("do tego ekranu pasowały.")


def test_single_unfinished_fragment_gets_ellipsis() -> None:
    assert summarize("Już 24 października ruszy trzecia edycja testu, czyli") == (
        "Już 24 października ruszy trzecia edycja testu, czyli…"
    )


def test_overlong_first_sentence_cut_at_word() -> None:
    text = "word " * 100 + "end."
    summary = summarize(text, max_chars=50)
    assert len(summary) <= 50
    assert summary.endswith("word…")


@pytest.mark.parametrize(
    "text, count",
    [
        ("The U.S. Army said so. Then it left.", 2),
        ("Sprawa ws. Ziobry trwa. Sąd orzekł.", 2),
        ("Byli tam m.in. posłowie PiS. Potem wyszli.", 2),
        ("W 2025 r. rząd przyjął plan. Plan upadł.", 2),
        ("Dr. Smith spoke. Prof. Jones replied!", 2),
        ('He said "stop." Then he left.', 2),
        ("Kosztowało to 5 tys. zł. Dużo?", 2),
    ],
)
def test_sentence_split_respects_abbreviations(text: str, count: int) -> None:
    assert len(sentences(text)) == count, sentences(text)


def item(title: str, text: str) -> Item:
    return Item(1, "hn", title, "https://x", None, text, datetime(2026, 10, 29, tzinfo=UTC),
                None, None)  # fmt: skip


def test_story_summary_uses_first_item_with_text() -> None:
    lead = item("What we know so far about Spain train crash", "")
    other = item("Spain crash", BBC_TAPES)
    story = RankedStory(1, "en", lead, (other,), 1.0, 1.0, 1.0, 1.0, None)
    assert story_summary(story) == BBC_TAPES

    alone = RankedStory(2, "en", lead, (), 1.0, 1.0, 1.0, 1.0, None)
    assert story_summary(alone) == ""


def test_empty_text() -> None:
    assert summarize("") == ""
