"""Local web view of the Markdown digests: `/`, `/d/YYYY-MM-DD`, `/archive`.

Routing is a pure function over the digests directory; the HTTP server only wraps
it and listens on 127.0.0.1. Raw HTML in the Markdown is never rendered.
"""

import html
import re
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from markdown_it import MarkdownIt

DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
HOST = "127.0.0.1"

_md = MarkdownIt("commonmark", {"html": False})


def _external_link(renderer, tokens, idx, options, env) -> str:
    tokens[idx].attrSet("target", "_blank")
    tokens[idx].attrSet("rel", "noopener noreferrer")
    return renderer.renderToken(tokens, idx, options, env)


_md.add_render_rule("link_open", _external_link)

STYLE = """
:root { --bg: #fbfaf7; --fg: #1d1d1f; --muted: #6b6b70; --link: #1a55b8; --line: #e4e2dc; }
@media (prefers-color-scheme: dark) {
  :root { --bg: #17181b; --fg: #e8e6e1; --muted: #9a9aa2; --link: #8db4ff; --line: #2c2e33; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--fg);
  font: 16px/1.55 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 46rem; margin: 0 auto; padding: 1rem 1rem 4rem; }
nav { display: flex; gap: 1rem; flex-wrap: wrap; padding: .75rem 0; font-size: .9rem;
  border-bottom: 1px solid var(--line); }
nav .spacer { flex: 1; }
a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }
h1 { font-size: 1.6rem; margin: 1.2rem 0 .3rem; }
h2 { font-size: 1.15rem; margin: 2rem 0 .5rem; padding-bottom: .3rem;
  border-bottom: 1px solid var(--line); }
em { color: var(--muted); font-style: normal; font-size: .88rem; }
ul { padding-left: 1.1rem; }
li { margin: .55rem 0; }
li li { margin: .2rem 0; font-size: .92rem; }
strong a { color: var(--fg); }
p { margin: .4rem 0; }
code { font-size: .88em; }
.archive li { margin: .3rem 0; }
"""


@dataclass(frozen=True)
class Response:
    status: int
    body: str
    content_type: str = "text/html; charset=utf-8"


def digest_dates(directory: Path) -> list[str]:
    """Dates of the digest files, newest first."""
    if not directory.is_dir():
        return []
    return sorted((p.stem for p in directory.glob("*.md") if DATE.fullmatch(p.stem)), reverse=True)


def _page(title: str, body: str, nav: str) -> str:
    return (
        '<!doctype html>\n<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{html.escape(title)}</title><style>{STYLE}</style></head>"
        f"<body><main><nav>{nav}</nav>{body}</main></body></html>\n"
    )


def _nav(dates: list[str], current: str | None) -> str:
    links = [
        '<a href="/">Latest</a>',
        '<a href="/archive">Archive</a>',
        '<span class="spacer"></span>',
    ]
    if current in dates:
        i = dates.index(current)
        if i + 1 < len(dates):
            links.append(f'<a href="/d/{dates[i + 1]}">← {dates[i + 1]}</a>')
        if i > 0:
            links.append(f'<a href="/d/{dates[i - 1]}">{dates[i - 1]} →</a>')
    return " ".join(links)


def render_markdown(text: str) -> str:
    return _md.render(text)


def route(path: str, directory: Path) -> Response:
    path = path.split("?", 1)[0].rstrip("/") or "/"
    dates = digest_dates(directory)

    if path == "/archive":
        items = "".join(f'<li><a href="/d/{d}">{d}</a></li>' for d in dates)
        body = f'<h1>Archive</h1><ul class="archive">{items or "<li>No digests yet.</li>"}</ul>'
        return Response(200, _page("Everyday News – archive", body, _nav(dates, None)))

    if path == "/":
        if not dates:
            body = "<h1>No digest yet</h1><p>Run <code>news run</code> to make the first one.</p>"
            return Response(200, _page("Everyday News", body, _nav(dates, None)))
        date = dates[0]
    elif path.startswith("/d/") and DATE.fullmatch(path[3:]) and path[3:] in dates:
        date = path[3:]
    else:
        body = f"<h1>Not found</h1><p>{html.escape(path)}</p>"
        return Response(404, _page("Not found", body, _nav(dates, None)))

    text = (directory / f"{date}.md").read_text(encoding="utf-8")
    return Response(200, _page(f"Everyday News – {date}", render_markdown(text), _nav(dates, date)))


def serve(directory: Path, port: int) -> ThreadingHTTPServer:
    """A server for the digests in `directory` on 127.0.0.1 (call serve_forever())."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (http.server naming)
            response = route(self.path, directory)
            body = response.body.encode("utf-8")
            self.send_response(response.status)
            self.send_header("Content-Type", response.content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # quiet console
            pass

    return ThreadingHTTPServer((HOST, port), Handler)
