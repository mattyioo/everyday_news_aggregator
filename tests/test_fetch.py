from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from everyday_news import db
from everyday_news.fetch import (
    COOLDOWN,
    ERROR_COOLDOWN,
    PAUSE_SECONDS,
    USER_AGENT,
    fetch_all,
    make_client,
)
from everyday_news.sources import Source

FIXTURES = Path(__file__).parent / "fixtures"
T0 = datetime(2026, 10, 29, 12, 0, tzinfo=UTC)


def source(id: str, enabled: bool = True) -> Source:
    return Source(id=id, name=id, url=f"https://{id}.example/feed", lang="en", enabled=enabled)


def fixture(id: str) -> bytes:
    return (FIXTURES / f"{id}.xml").read_bytes()


class Server:
    """Mock transport that records every request and answers per host."""

    def __init__(self, handler: Callable[[httpx.Request], httpx.Response]) -> None:
        self.requests: list[httpx.Request] = []
        self.handler = handler

    def client(self) -> httpx.Client:
        def record(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return self.handler(request)

        return make_client(httpx.MockTransport(record))


def serve_fixtures(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, content=fixture(request.url.host.removesuffix(".example")))


@pytest.fixture
def conn(tmp_path: Path):
    c = db.connect(tmp_path / "news.db")
    yield c
    c.close()


def run(sources, conn, server, *, at=T0, force=False, sleeps=None):
    with server.client() as client:
        return fetch_all(
            sources,
            conn,
            client,
            force=force,
            now=lambda: at,
            sleep=(sleeps.append if sleeps is not None else lambda s: None),
        )


ALL = ["hn", "reddit-technology", "wp", "znosnenewsy"]


def test_fetches_each_source_once_with_pauses_and_user_agent(conn) -> None:
    server, sleeps = Server(serve_fixtures), []
    results = run([source(i) for i in ALL], conn, server, sleeps=sleeps)

    assert [r.status for r in results] == ["200"] * 4
    assert len(server.requests) == 4
    assert all(r.headers["user-agent"] == USER_AGENT for r in server.requests)
    assert sleeps == [PAUSE_SECONDS] * 3  # between requests, not before the first
    assert conn.execute("SELECT COUNT(*) FROM raw_item").fetchone()[0] == 12


def test_parses_real_feed_formats(conn) -> None:
    run([source(i) for i in ALL], conn, Server(serve_fixtures))
    rows = {
        r["source_id"]: r
        for r in conn.execute("SELECT * FROM raw_item GROUP BY source_id ORDER BY id")
    }
    # HN items have no <guid>: the link is used instead, comments URL kept separately
    assert rows["hn"]["guid"] == rows["hn"]["url"]
    assert rows["hn"]["comments_url"].startswith("https://news.ycombinator.com/item?id=")
    assert rows["reddit-technology"]["guid"].startswith("t3_")
    for r in rows.values():
        assert r["title"] and r["url"].startswith("https://")
        assert datetime.fromisoformat(r["published"]).tzinfo is not None


def test_refetch_does_not_duplicate_rows(conn) -> None:
    server = Server(serve_fixtures)
    run([source("wp")], conn, server)
    results = run([source("wp")], conn, server, at=T0 + COOLDOWN, force=True)
    assert results[0].detail == "3 items (0 new)"
    assert conn.execute("SELECT COUNT(*) FROM raw_item").fetchone()[0] == 3


def test_cooldown_skips_without_request(conn) -> None:
    server = Server(serve_fixtures)
    run([source("hn")], conn, server)
    results = run([source("hn")], conn, server, at=T0 + timedelta(minutes=5))
    assert results[0].status == "skipped"
    assert "cooldown (11 min left)" == results[0].detail
    assert len(server.requests) == 1

    run([source("hn")], conn, server, at=T0 + COOLDOWN)
    assert len(server.requests) == 2


def test_force_ignores_cooldown(conn) -> None:
    server = Server(serve_fixtures)
    run([source("hn")], conn, server)
    run([source("hn")], conn, server, at=T0 + timedelta(minutes=1), force=True)
    assert len(server.requests) == 2


def test_conditional_get_and_304(conn) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.headers.get("if-none-match") == '"v1"':
            return httpx.Response(304)
        return httpx.Response(
            200,
            content=fixture("znosnenewsy"),
            headers={"ETag": '"v1"', "Last-Modified": "Thu, 29 Oct 2026 11:00:59 GMT"},
        )

    server = Server(handler)
    run([source("znosnenewsy")], conn, server)
    results = run([source("znosnenewsy")], conn, server, at=T0 + COOLDOWN)

    second = server.requests[1]
    assert second.headers["if-none-match"] == '"v1"'
    assert second.headers["if-modified-since"] == "Thu, 29 Oct 2026 11:00:59 GMT"
    assert results[0].status == "304"
    # 304 keeps the validators for next time
    state = conn.execute("SELECT etag FROM fetch_state").fetchone()
    assert state["etag"] == '"v1"'


@pytest.mark.parametrize(
    "response, detail",
    [
        (httpx.Response(429), "HTTP 429"),
        (httpx.Response(503), "HTTP 503"),
        (httpx.Response(301, headers={"Location": "https://elsewhere/"}), "HTTP 301"),
    ],
)
def test_bad_status_skips_source_without_retry(conn, response, detail) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "bad.example":
            return response
        return serve_fixtures(request)

    server = Server(handler)
    results = run([source("bad"), source("hn")], conn, server)

    assert [(r.status, r.detail) for r in results] == [
        ("error", detail),
        ("200", "3 items (3 new)"),
    ]
    assert [r.url.host for r in server.requests] == ["bad.example", "hn.example"]


def test_network_error_is_isolated_and_counts_toward_cooldown(conn) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "bad.example":
            raise httpx.ConnectTimeout("timed out", request=request)
        return serve_fixtures(request)

    server = Server(handler)
    results = run([source("bad"), source("hn")], conn, server)
    assert (results[0].status, results[0].detail) == ("error", "ConnectTimeout")
    assert results[1].status == "200"

    # Failed sources back off longer than the normal cooldown
    again = run([source("bad")], conn, server, at=T0 + COOLDOWN)
    assert (again[0].status, again[0].detail) == ("skipped", "backoff after error (46 min left)")
    assert len(server.requests) == 2

    run([source("bad")], conn, server, at=T0 + ERROR_COOLDOWN)
    assert len(server.requests) == 3


def test_disabled_source_is_never_requested(conn) -> None:
    server = Server(serve_fixtures)
    results = run([source("hn", enabled=False)], conn, server)
    assert (results[0].status, results[0].detail) == ("skipped", "disabled")
    assert server.requests == []
