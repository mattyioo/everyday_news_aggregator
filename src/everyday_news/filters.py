"""Rule-based noise filters from `filters.toml`: muted words and headline rules.

Each article gets at most one verdict ("drop" or "downrank") with a reason;
articles without a verdict are kept as they are. Drop beats downrank, and the
first matching rule of the strongest action wins.
"""

import re
import sqlite3
import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = Path("filters.toml")
ACTIONS = ("drop", "downrank")
LANGS = ("en", "pl", "any")
PREFIX_MIN = 4

WORD = re.compile(r"\w+")


class FilterConfigError(ValueError):
    """Raised when `filters.toml` is missing or invalid."""


@dataclass(frozen=True)
class Rule:
    lang: str
    pattern: re.Pattern[str]
    action: str
    reason: str


@dataclass(frozen=True)
class Filters:
    muted: tuple[str, ...]
    rules: tuple[Rule, ...]


@dataclass(frozen=True)
class Verdict:
    action: str
    reason: str


def load_filters(path: Path = DEFAULT_PATH) -> Filters:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FilterConfigError(f"{path}: file not found") from None
    except tomllib.TOMLDecodeError as e:
        raise FilterConfigError(f"{path}: invalid TOML: {e}") from None

    muted = data.get("muted", [])
    if not isinstance(muted, list) or not all(isinstance(m, str) for m in muted):
        raise FilterConfigError(f"{path}: muted must be a list of strings")
    for m in muted:
        if not WORD.fullmatch(m):
            raise FilterConfigError(f"{path}: muted word {m!r} must be a single word")

    rules = [_parse_rule(r, path, i) for i, r in enumerate(data.get("rule", []), start=1)]
    return Filters(muted=tuple(m.casefold() for m in muted), rules=tuple(rules))


def _parse_rule(entry: dict, path: Path, index: int) -> Rule:
    where = f"{path}: rule #{index}"
    for key in ("lang", "pattern", "action", "reason"):
        if not isinstance(entry.get(key), str) or not entry[key].strip():
            raise FilterConfigError(f"{where}: missing or empty {key!r}")
    if entry["lang"] not in LANGS:
        raise FilterConfigError(f"{where}: lang must be one of {LANGS}")
    if entry["action"] not in ACTIONS:
        raise FilterConfigError(f"{where}: action must be one of {ACTIONS}")
    try:
        pattern = re.compile(entry["pattern"], re.IGNORECASE)
    except re.error as e:
        raise FilterConfigError(f"{where}: invalid pattern: {e}") from None
    return Rule(entry["lang"], pattern, entry["action"], entry["reason"])


def evaluate(title: str, text: str, lang: str, filters: Filters) -> Verdict | None:
    """Return the verdict for one article, or None to keep it as is."""
    for word in WORD.findall(f"{title} {text}".casefold()):
        for m in filters.muted:
            if word.startswith(m) if len(m) >= PREFIX_MIN else word == m:
                return Verdict("drop", f"muted: {m}")

    matches = [r for r in filters.rules if r.lang in (lang, "any") and r.pattern.search(title)]
    for action in ACTIONS:
        for r in matches:
            if r.action == action:
                return Verdict(r.action, r.reason)
    return None


def apply_filters(conn: sqlite3.Connection, filters: Filters) -> int:
    """Recompute verdicts for all articles. Returns how many are dropped."""
    conn.execute("DELETE FROM article_verdict")
    dropped = 0
    for row in conn.execute("SELECT id, lang, title, text FROM article").fetchall():
        verdict = evaluate(row["title"], row["text"], row["lang"], filters)
        if verdict:
            conn.execute(
                "INSERT INTO article_verdict (article_id, action, reason) VALUES (?, ?, ?)",
                (row["id"], verdict.action, verdict.reason),
            )
            dropped += verdict.action == "drop"
    conn.commit()
    return dropped
