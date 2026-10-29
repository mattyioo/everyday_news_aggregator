"""Mark exact duplicates: same canonical URL, or same title in the same language.

Duplicates are linked into groups (A shares a URL with B, B shares a title
with C: all three are one group). Each group shows one primary article; the
rest point at it via `duplicate_of` and keep their rows, so their discussion
links stay available.
"""

import sqlite3

from everyday_news.sources import Source


def mark_duplicates(conn: sqlite3.Connection, sources: list[Source]) -> int:
    """Recompute `duplicate_of` for all articles. Returns how many are duplicates."""
    weights = {s.id: s.weight for s in sources}
    rows = conn.execute(
        "SELECT id, source_id, lang, url, title_hash, published_at, duplicate_of FROM article"
    ).fetchall()

    parent = {row["id"]: row["id"] for row in rows}

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    first_with: dict[tuple, int] = {}
    for row in rows:
        for key in (("url", row["url"]), ("title", row["lang"], row["title_hash"])):
            if key in first_with:
                parent[find(row["id"])] = find(first_with[key])
            else:
                first_with[key] = row["id"]

    groups: dict[int, list[sqlite3.Row]] = {}
    for row in rows:
        groups.setdefault(find(row["id"]), []).append(row)

    duplicates = 0
    for members in groups.values():
        # Primary: most trusted source, then first published, then first stored.
        primary = min(
            members,
            key=lambda r: (-weights.get(r["source_id"], 0.0), r["published_at"], r["id"]),
        )
        for row in members:
            target = None if row is primary else primary["id"]
            if row["duplicate_of"] != target:
                conn.execute(
                    "UPDATE article SET duplicate_of = ? WHERE id = ?", (target, row["id"])
                )
            duplicates += target is not None
    conn.commit()
    return duplicates
