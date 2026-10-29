"""Load app settings from `settings.toml`."""

import tomllib
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PATH = Path("settings.toml")


class SettingsError(ValueError):
    """Raised when `settings.toml` is missing or invalid."""


@dataclass(frozen=True)
class Settings:
    retention_days: int = 30
    digest_hours: int = 24
    stories_per_site: int = 10


def load_settings(path: Path = DEFAULT_PATH) -> Settings:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SettingsError(f"{path}: file not found") from None
    except tomllib.TOMLDecodeError as e:
        raise SettingsError(f"{path}: invalid TOML: {e}") from None

    days = _whole_number(data, "retention_days", Settings.retention_days, 1, 3650, path)
    hours = _whole_number(data, "digest_hours", Settings.digest_hours, 1, 24 * 30, path)
    per_site = _whole_number(data, "stories_per_site", Settings.stories_per_site, 1, 100, path)
    return Settings(retention_days=days, digest_hours=hours, stories_per_site=per_site)


def _whole_number(data: dict, key: str, default: int, low: int, high: int, path: Path) -> int:
    value = data.get(key, default)
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise SettingsError(f"{path}: {key} must be a whole number from {low} to {high}")
    return value
