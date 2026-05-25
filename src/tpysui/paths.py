#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from pathlib import Path


def settings_dir() -> Path:
    return Path.home() / ".tpysui"


def settings_path() -> Path:
    return settings_dir() / "tpysui_setting.toml"
