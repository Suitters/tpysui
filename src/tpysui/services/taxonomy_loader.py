#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-

"""Taxonomy loader — loads, validates, and builds the command registry."""

from __future__ import annotations
import importlib
import json
import logging
from dataclasses import dataclass
from importlib.resources import files

import jsonschema

from tpysui.paths import settings_dir

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NamedFieldSpec:
    """One field within a named compound kind."""

    name: str
    kind: KindSpec
    optional: bool
    source: str


@dataclass(frozen=True)
class KindSpec:
    """Type and shape of a value as defined in taxonomy."""

    type: str  # "scalar" | "compound"
    validation: str | None = None  # scalar only
    shape: str | None = None  # compound only: "named" | "keyed"
    fields: tuple[NamedFieldSpec, ...] | None = None  # named compound
    key_kind: KindSpec | None = None  # keyed compound
    value_kind: KindSpec | None = None  # keyed compound


@dataclass(frozen=True)
class ArgSpec:
    """One argument definition as loaded from the taxonomy."""

    name: str
    kind: KindSpec
    optional: bool
    default: tuple  # () absent | (x,) pre-populate | (x, y, ...) static select
    source: str  # "none" | "group_addresses" | "owned_objects" | "owned_coins"
    multiple: bool
    min_items: int | None = None  # required when multiple=True


@dataclass(frozen=True)
class CommandEntry:
    """One command definition as loaded from the taxonomy."""

    name: str
    source_module: str
    group: str
    mode: str  # "read" | "write"
    pageable: bool
    args: tuple[ArgSpec, ...]


def _parse_kind(data: dict) -> KindSpec:
    if data["type"] == "scalar":
        return KindSpec(type="scalar", validation=data["validation"])
    if data["shape"] == "named":
        return KindSpec(
            type="compound",
            shape="named",
            fields=tuple(_parse_named_field(f) for f in data["fields"]),
        )
    return KindSpec(
        type="compound",
        shape="keyed",
        key_kind=_parse_kind(data["key_kind"]),
        value_kind=_parse_kind(data["value_kind"]),
    )


def _parse_named_field(data: dict) -> NamedFieldSpec:
    return NamedFieldSpec(
        name=data["name"],
        kind=_parse_kind(data["kind"]),
        optional=data["optional"],
        source=data["source"],
    )


def _parse_arg(data: dict) -> ArgSpec:
    return ArgSpec(
        name=data["name"],
        kind=_parse_kind(data["kind"]),
        optional=data["optional"],
        default=tuple(data["default"]),
        source=data["source"],
        multiple=data["multiple"],
        min_items=data.get("min_items"),
    )


def _parse_command(data: dict) -> CommandEntry:
    return CommandEntry(
        name=data["name"],
        source_module=data["source_module"],
        group=data["group"],
        mode=data["mode"],
        pageable=data["pageable"],
        args=tuple(_parse_arg(a) for a in data["args"]),
    )


def _verify_command(entry: CommandEntry, fatal: bool) -> bool:
    """Verify source_module is importable and name exists within it."""
    try:
        mod = importlib.import_module(entry.source_module)
    except ModuleNotFoundError as exc:
        msg = f"Command '{entry.name}': module '{entry.source_module}' not importable: {exc}"
        if fatal:
            raise RuntimeError(msg) from exc
        logger.warning(msg)
        return False
    if not hasattr(mod, entry.name):
        msg = f"Command '{entry.name}' not found in module '{entry.source_module}'"
        if fatal:
            raise RuntimeError(msg)
        logger.warning(msg)
        return False
    return True


def load_command_registry() -> dict[str, CommandEntry]:
    """Load, validate, and return the command registry.

    Loads pysui_commands.json (fatal on failure) then user_commands.json
    from ~/.tpysui/ (warn+skip on failure). User commands override pysui
    commands on name collision with a warning.
    """
    schema_ref = files("tpysui") / "data" / "taxonomy.json"
    with schema_ref.open("r") as fh:
        schema = json.load(fh)

    cmds_ref = files("tpysui") / "data" / "pysui_commands.json"
    with cmds_ref.open("r") as fh:
        pysui_data = json.load(fh)

    try:
        jsonschema.validate(instance=pysui_data, schema=schema)
    except jsonschema.ValidationError as exc:
        raise RuntimeError(f"pysui_commands.json invalid: {exc.message}") from exc

    registry: dict[str, CommandEntry] = {}
    for cmd_data in pysui_data["commands"]:
        entry = _parse_command(cmd_data)
        _verify_command(entry, fatal=True)
        registry[entry.name] = entry

    user_path = settings_dir() / "user_commands.json"
    if not user_path.exists():
        return registry

    try:
        with user_path.open("r") as fh:
            user_data = json.load(fh)
    except json.JSONDecodeError as exc:
        logger.warning(f"user_commands.json is not valid JSON: {exc} — skipping")
        return registry

    try:
        jsonschema.validate(instance=user_data, schema=schema)
    except jsonschema.ValidationError as exc:
        logger.warning(f"user_commands.json schema invalid: {exc.message} — skipping all user commands")
        return registry

    for cmd_data in user_data["commands"]:
        entry = _parse_command(cmd_data)
        if not _verify_command(entry, fatal=False):
            continue
        if entry.name in registry:
            logger.warning(
                f"User command '{entry.name}' overrides pysui built-in "
                f"from '{registry[entry.name].source_module}'"
            )
        registry[entry.name] = entry

    return registry
