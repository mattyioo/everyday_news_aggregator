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


def load_settings(path: Path = DEFAULT_PATH) -> Settings:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SettingsError(f"{path}: file not found") from None
    except tomllib.TOMLDecodeError as e:
        raise SettingsError(f"{path}: invalid TOML: {e}") from None

    days = data.get("retention_days", Settings.retention_days)
    if not isinstance(days, int) or isinstance(days, bool) or not 1 <= days <= 3650:
        raise SettingsError(f"{path}: retention_days must be a whole number from 1 to 3650")
    return Settings(retention_days=days)
