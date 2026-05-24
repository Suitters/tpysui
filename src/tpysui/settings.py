import sys
from dataclasses import dataclass, field

from .paths import settings_path

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib  # type: ignore[no-redef]

import tomli_w


@dataclass
class Settings:
    faux_mode: bool = True
    default_config_path: str | None = None
    known_configs: list[dict] = field(default_factory=list)


def load_settings() -> Settings:
    path = settings_path()
    if not path.exists():
        s = Settings()
        save_settings(s)
        return s
    with path.open("rb") as f:
        data = tomllib.load(f)
    return Settings(
        faux_mode=data.get("dev", {}).get("faux_mode", True),
        default_config_path=data.get("configs", {}).get("default"),
        known_configs=data.get("configs", {}).get("known", []),
    )


def save_settings(s: Settings) -> None:
    path = settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    configs: dict = {"known": s.known_configs}
    if s.default_config_path is not None:
        configs["default"] = s.default_config_path
    payload: dict = {
        "dev": {"faux_mode": s.faux_mode},
        "configs": configs,
    }
    with path.open("wb") as f:
        tomli_w.dump(payload, f)
