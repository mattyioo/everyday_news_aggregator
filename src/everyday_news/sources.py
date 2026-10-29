"""Load and validate news sources from `sources.toml`."""

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

LANGUAGES = ("en", "pl")
DEFAULT_PATH = Path("sources.toml")


class SourceConfigError(ValueError):
    """Raised when `sources.toml` is missing or invalid."""


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    url: str
    lang: str
    weight: float = 1.0
    tags: tuple[str, ...] = field(default_factory=tuple)
    enabled: bool = True
    fetch_fulltext: bool = False
    digest_hours: int | None = None  # overrides settings.toml for this site


def load_sources(path: Path = DEFAULT_PATH) -> list[Source]:
    """Read every `[[source]]` entry from `path`, enabled or not."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SourceConfigError(f"{path}: file not found") from None
    except tomllib.TOMLDecodeError as e:
        raise SourceConfigError(f"{path}: invalid TOML: {e}") from None

    entries = data.get("source", [])
    if not isinstance(entries, list) or not entries:
        raise SourceConfigError(f"{path}: no [[source]] entries")

    sources = [_parse(entry, path, i) for i, entry in enumerate(entries, start=1)]

    seen: set[str] = set()
    for s in sources:
        if s.id in seen:
            raise SourceConfigError(f"{path}: duplicate source id {s.id!r}")
        seen.add(s.id)
    return sources


def _parse(entry: dict, path: Path, index: int) -> Source:
    where = f"{path}: source #{index}"
    for key in ("id", "name", "url", "lang"):
        value = entry.get(key)
        if not isinstance(value, str) or not value.strip():
            raise SourceConfigError(f"{where}: missing or empty {key!r}")
    where = f"{path}: source {entry['id']!r}"

    if entry["lang"] not in LANGUAGES:
        raise SourceConfigError(f"{where}: lang must be one of {LANGUAGES}, got {entry['lang']!r}")
    if not entry["url"].startswith(("http://", "https://")):
        raise SourceConfigError(f"{where}: url must start with http:// or https://")

    weight = entry.get("weight", 1.0)
    if not isinstance(weight, int | float) or isinstance(weight, bool) or not 0 <= weight <= 2:
        raise SourceConfigError(f"{where}: weight must be a number between 0 and 2")

    tags = entry.get("tags", [])
    if not isinstance(tags, list) or not all(isinstance(t, str) for t in tags):
        raise SourceConfigError(f"{where}: tags must be a list of strings")

    for key in ("enabled", "fetch_fulltext"):
        if key in entry and not isinstance(entry[key], bool):
            raise SourceConfigError(f"{where}: {key} must be true or false")

    digest_hours = entry.get("digest_hours")
    if digest_hours is not None and (
        not isinstance(digest_hours, int)
        or isinstance(digest_hours, bool)
        or not 1 <= digest_hours <= 720
    ):
        raise SourceConfigError(f"{where}: digest_hours must be a whole number from 1 to 720")

    return Source(
        id=entry["id"],
        name=entry["name"],
        url=entry["url"],
        lang=entry["lang"],
        weight=float(weight),
        tags=tuple(tags),
        enabled=entry.get("enabled", True),
        fetch_fulltext=entry.get("fetch_fulltext", False),
        digest_hours=digest_hours,
    )
