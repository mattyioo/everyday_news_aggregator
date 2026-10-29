# 0018 – Log

## 2026-10-29
- User asked for the web view. Planned as an optional Phase 5 item; now built.
- `markdown-it-py` added (CommonMark, `html: False`; its link validation drops `javascript:`).
- First test run: render rule had the wrong argument order (markdown-it-py passes the
  renderer first); fixed.
- `news web` = `news run` (unless `--no-fetch`) + `ThreadingHTTPServer` on 127.0.0.1,
  opens the browser (unless `--no-open`), Ctrl+C stops. No fetching while it runs.
- Real check over HTTP on the actual digests (ephemeral port): `/` 200 with Following,
  4 site sections and Filtered out, 🆕/📌 badges, 50 external links with target=_blank;
  `/archive` and `/d/2026-10-29` 200; `/d/../etc/passwd` and `/nope` 404; bound to 127.0.0.1.
- Tests: 143 passed (11 new). Verified and archived.
