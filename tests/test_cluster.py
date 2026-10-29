from pathlib import Path

import pytest

from everyday_news import db
from everyday_news.cluster import cluster, key_words
from everyday_news.normalize import title_hash
from everyday_news.sources import Source

SOURCES = [
    Source(id="bbc", name="BBC", url="https://bbc.example/f", lang="en", weight=1.0),
    Source(id="hn", name="HN", url="https://hn.example/f", lang="en", weight=0.9),
    Source(id="wp", name="WP", url="https://wp.example/f", lang="pl", weight=0.7),
    Source(id="zn", name="ZN", url="https://zn.example/f", lang="pl", weight=1.0),
]
LANG = {s.id: s.lang for s in SOURCES}

# Real headlines and leads from news.db, 2026-10-29
REAL = [
    ("bbc", "2026-10-28T16:45", "Watch: At the scene of Spain's deadly train crash",
     "People have been killed after a Spanish high-speed train collided with another train "
     "south of the capital Madrid, making this the country's worst disaster since 2013."),
    ("hn", "2026-10-29T08:55", "What we know so far about Spain train crash", ""),
    ("bbc", "2026-10-29T10:02", "What we know so far about deadly Spain train crash",
     "More than 500 passengers were on board the trains when the crash occurred in the "
     "province of Toledo, south of Madrid."),
    ("bbc", "2026-10-29T11:07",
     "Audio reveals exchanges between Spain train operators and drivers moments before "
     "deadly crash",
     "The leaked tapes appear to show one high-speed train was given clearance to move at "
     "normal speed, even though another up ahead had stalled."),
    ("bbc", "2026-10-29T13:25",
     "Philippine police obtain warrant to search Thomas Markle's devices",
     "Images of child sexual abuse allegedly belonging to Meghan's father had reportedly been "
     "found in his former home in the Philippines."),
    ("bbc", "2026-10-29T14:49",
     "Watch: VHS tapes and computers handed to police as Thomas Markle is investigated",
     "The BBC's Jonathan Head is in Cebu, reporting from outside the home where Markle resided."),
    ("bbc", "2026-10-29T09:06", "How could Israel break election deadlock? Here are four scenarios",
     "With more than 90% of votes counted, all signs point to an impasse. The most likely "
     "outcome may be new elections."),
    ("bbc", "2026-10-29T15:47",
     "Netanyahu's bloc leading Israel election but short of majority, partial results show",
     "With 99% of ballots counted, Netanyahu's Likud party and its allies are set to win 53 "
     "seats in the 120-seat Knesset."),
    ("bbc", "2026-10-28T21:16",
     "Death of US actress Hayden Panettiere ruled accidental, ending local police probe",
     "The Heroes and Nashville star died in August from the toxic effects of fentanyl, Xanax "
     "and several other drugs."),
    ("hn", "2026-10-29T16:41", "Toxic Experts", ""),
    ("zn", "2026-10-20T12:44", "The Great Folding Test – test iPhona Duo już za chwilę",
     "Już 24 października, o godzinie 14:00, ruszy trzecia edycja The Great Folding Test, "
     "czyli Wielkiego Testu Składania na kanale YT"),
    ("zn", "2026-10-25T20:51", "Jak apki wykorzystują potencjał iPhona Duo?",
     "Potencjał ekranowy oczywiście, bo chodzi tu o wymiary i o kodowanie aplikacji, aby do "
     "tego ekranu pasowały. TechCrunch przygotował ciekawe"),
    ("zn", "2026-10-26T18:51", "Porażka iPhona Duo? The Great Folding Test III",
     "Wielki Test Składania III – czyli live u Kuby, gdzie testowaliśmy wytrzymałość iPhona "
     "Duo, skończył się wcześniej, niż myśleliśmy. Duo"),
    ("wp", "2026-10-29T16:02", "Aż 1,5 mln wyświetleń. Polska zachwyca się filmem z budowy",
     "Drogowcy zakończyli betonowanie ustroju nośnego najwyższej estakady w Polsce, która "
     "powstaje na podkarpackim odcinku trasy S19 Babica – Jawornik. Z tej okazji GDDKiA "
     "opublikowała spektakularne nagranie z drona, pokazujące gigantyczną konstrukcję."),
    ("wp", "2026-10-29T17:01", "Budują najwyższą estakadę w Polsce. Nagranie z S19",
     "Na Podkarpaciu zakończyło się betonowanie ustroju nośnego estakady ES-26 na odcinku S19 "
     "Babica–Jawornik. Według dostępnych informacji obiekt będzie najwyższą estakadą w Polsce."),
    ("wp", "2026-10-29T15:36", "Zełenski otwiera się na ustępstwa",
     "Zełenski mówił przez ostatnie trzy lata, że Rosjanie mają się wycofać."),
]  # fmt: skip


@pytest.fixture
def conn(tmp_path: Path):
    c = db.connect(tmp_path / "news.db")
    yield c
    c.close()


def add(conn, source: str, published: str, title: str, text: str = "") -> int:
    n = conn.execute("SELECT COUNT(*) FROM article").fetchone()[0]
    return conn.execute(
        "INSERT INTO article (raw_item_id, source_id, lang, url, title, text, published_at,"
        " title_hash) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (n + 1, source, LANG[source], f"https://x/{n}", title, text,
         f"{published}:00+00:00", title_hash(title)),
    ).lastrowid  # fmt: skip


def groups(conn) -> set[frozenset[str]]:
    """Stories as sets of article titles."""
    rows = conn.execute(
        "SELECT story_id, title FROM story_article JOIN article ON article.id = article_id"
    )
    by_story: dict[int, set[str]] = {}
    for r in rows:
        by_story.setdefault(r["story_id"], set()).add(r["title"])
    return {frozenset(g) for g in by_story.values()}


def titles(*prefixes: str) -> frozenset[str]:
    found = frozenset(t for _, _, t, _ in REAL if t.startswith(prefixes))
    assert len(found) == len(prefixes)
    return found


def test_real_same_event_groups(conn) -> None:
    for item in REAL:
        add(conn, *item)
    assert cluster(conn, SOURCES) == len(REAL)

    multi = {g for g in groups(conn) if len(g) > 1}
    assert multi == {
        titles("Watch: At the scene", "What we know so far about Spain",
               "What we know so far about deadly", "Audio reveals"),
        titles("Philippine police", "Watch: VHS"),
        titles("How could Israel", "Netanyahu's bloc"),
        titles("Jak apki", "Porażka iPhona"),
        titles("Aż 1,5 mln", "Budują najwyższą"),
    }  # fmt: skip
    # "Toxic Experts" (no text) must not join the Panettiere story; the Oct 20 iPhone
    # announcement is 5 days before the rest and stays separate
    assert frozenset({"Toxic Experts"}) in groups(conn)
    assert titles("The Great Folding Test –") in groups(conn)


def test_rerun_assigns_nothing_and_keeps_ids(conn) -> None:
    for item in REAL[:4]:
        add(conn, *item)
    cluster(conn, SOURCES)
    before = conn.execute("SELECT * FROM story_article ORDER BY article_id").fetchall()
    assert cluster(conn, SOURCES) == 0

    add(conn, "bbc", "2026-10-29T18:00", "Spain train crash: drivers questioned")
    assert cluster(conn, SOURCES) == 1
    after = conn.execute("SELECT * FROM story_article ORDER BY article_id").fetchall()
    assert [tuple(r) for r in after[:4]] == [tuple(r) for r in before]
    assert len({r["story_id"] for r in after}) == 1


def test_languages_never_mix(conn) -> None:
    add(conn, "bbc", "2026-10-29T10:00", "Apple MacBook Pro M6 launch")
    add(conn, "zn", "2026-10-29T11:00", "Apple MacBook Pro M6 launch")
    cluster(conn, SOURCES)
    langs = [r[0] for r in conn.execute("SELECT lang FROM story ORDER BY lang")]
    assert langs == ["en", "pl"]


def test_rolling_window(conn) -> None:
    add(conn, "bbc", "2026-10-20T10:00", "Ebola outbreak spreads in Congo")
    add(conn, "bbc", "2026-10-22T10:00", "Ebola outbreak reaches Congo capital")  # +2 days
    add(conn, "bbc", "2026-10-25T09:00", "Ebola outbreak Congo vaccine trial")  # +3 after newest
    add(conn, "bbc", "2026-10-29T10:00", "Ebola outbreak Congo death toll rises")  # +4: new story
    cluster(conn, SOURCES)
    sizes = sorted(len(g) for g in groups(conn))
    assert sizes == [1, 3]


def test_story_title_from_highest_weight_source(conn) -> None:
    add(conn, "hn", "2026-10-29T08:00", "What we know so far about Spain train crash")
    add(conn, "bbc", "2026-10-29T09:00", "What we know so far about deadly Spain train crash")
    cluster(conn, SOURCES)
    story = conn.execute("SELECT * FROM story").fetchone()
    assert story["title"] == "What we know so far about deadly Spain train crash"
    assert story["first_seen"].startswith("2026-10-29T08:00")
    assert story["last_updated"].startswith("2026-10-29T09:00")


def test_duplicates_and_deleted_articles_leave_their_story(conn) -> None:
    a = add(conn, "bbc", "2026-10-29T08:00", "Spain train crash toll rises")
    b = add(conn, "hn", "2026-10-29T09:00", "Spain train crash investigation")
    lone = add(conn, "wp", "2026-10-29T10:00", "Zełenski otwiera się na ustępstwa")
    cluster(conn, SOURCES)
    assert conn.execute("SELECT COUNT(*) FROM story").fetchone()[0] == 2

    conn.execute("UPDATE article SET duplicate_of = ? WHERE id = ?", (a, b))
    conn.execute("DELETE FROM article WHERE id = ?", (lone,))
    cluster(conn, SOURCES)
    assert groups(conn) == {frozenset({"Spain train crash toll rises"})}
    assert conn.execute("SELECT COUNT(*) FROM story").fetchone()[0] == 1


def test_key_words_stem_and_drop_stopwords() -> None:
    assert key_words("Porażka iPhona Duo?") == key_words("porażki iPhone duo")
    assert "s19" in key_words("Nagranie z S19")
    assert key_words("What we know so far about the") == set()
