from pathlib import Path


def settings_dir() -> Path:
    return Path.home() / ".tpysui"


def settings_path() -> Path:
    return settings_dir() / "settings.toml"
