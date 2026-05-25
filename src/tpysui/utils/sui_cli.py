#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

import json
from dataclasses import dataclass, field
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


@dataclass
class CliEnv:
    alias: str
    url: str


@dataclass
class CliKey:
    alias: str
    public_key: str


@dataclass
class CliConfig:
    active_env: str = ""
    envs: list[CliEnv] = field(default_factory=list)
    keys: list[CliKey] = field(default_factory=list)


def load_cli_config() -> CliConfig:
    sui_dir = Path.home() / ".sui" / "sui_config"
    client_yaml = sui_dir / "client.yaml"
    aliases_file = sui_dir / "sui.aliases"

    cfg = CliConfig()

    if client_yaml.exists() and yaml is not None:
        try:
            data = yaml.safe_load(client_yaml.read_text()) or {}
            cfg.active_env = data.get("active_env", "")
            for e in data.get("envs", []):
                alias = e.get("alias", "")
                url = e.get("rpc", "")
                if alias and url:
                    cfg.envs.append(CliEnv(alias=alias, url=url))
        except Exception:
            pass

    if aliases_file.exists():
        try:
            entries = json.loads(aliases_file.read_text()) or []
            for entry in entries:
                alias = entry.get("alias", "")
                pk = entry.get("public_key_base64", "")
                if alias and pk:
                    cfg.keys.append(CliKey(alias=alias, public_key=pk))
        except Exception:
            pass

    return cfg
