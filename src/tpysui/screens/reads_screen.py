#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Label, Select, TextArea

from ..services.base import (
    ActiveState,
    ArgInfo,
    CommandInfo,
    ReadResult,
)
from ..services.command_registry import COMMAND_LOOKUP, COMMAND_REGISTRY
from ..utils.validators import (
    valid_base58,
    valid_move_identifier,
    valid_sui_address,
    valid_type_tag,
    valid_unsigned_int,
)
from ..widgets.arg_widgets import (
    AddressSelect,
    ForVersionsWidget,
    MultiValueInput,
    ObjectChecklist,
    ObjectSelect,
    PlainInput,
)


def _make_arg_widget(arg: ArgInfo) -> Widget:
    t = arg.arg_type
    if t == "owner":
        return AddressSelect(label=arg.name, addresses=[])
    if t in ("object_id", "coin_id"):
        return ObjectSelect(label=arg.name)
    if t == "object_ids":
        return ObjectChecklist()
    if t == "for_versions":
        return ForVersionsWidget()
    if t == "coin_type":
        default = "0x2::sui::SUI" if arg.optional else ""
        return PlainInput(label=arg.name, validator=valid_type_tag, optional=arg.optional, default=default)
    if t == "object_type":
        return PlainInput(label=arg.name, validator=valid_type_tag, optional=arg.optional)
    if t in ("package", "package_address"):
        return PlainInput(label=arg.name, validator=valid_sui_address)
    if t in ("module_name", "type_name", "structure_name", "function_name"):
        return PlainInput(label=arg.name, validator=valid_move_identifier)
    if t == "name":
        return PlainInput(label=arg.name)
    if t == "digest":
        return PlainInput(label=arg.name, validator=valid_base58)
    if t == "digests":
        return MultiValueInput(label=arg.name, validator=valid_base58)
    if t in ("version", "sequence_number", "epoch_id"):
        return PlainInput(label=arg.name, validator=valid_unsigned_int, optional=arg.optional)
    return PlainInput(label=arg.name)


def _needs_objects(cmd_info: CommandInfo) -> bool:
    return any(a.arg_type in ("object_id", "coin_id", "object_ids", "for_versions") for a in cmd_info.args)


def _has_owner_arg(cmd_info: CommandInfo) -> bool:
    return any(a.arg_type == "owner" for a in cmd_info.args)


class ReadsScreen(Widget):
    """Area 2 — Blockchain Data Reads."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._current_cmd: str | None = None
        self._cursor: bytes | None = None
        self._last_state: ActiveState | None = None

    def compose(self) -> ComposeResult:
        options = [(c.name, c.name) for c in COMMAND_REGISTRY]
        with Vertical(id="reads_body"):
            with Horizontal(id="cmd_row"):
                yield Select(options, id="cmd_select", allow_blank=True, prompt="Select a read command…")
            with Horizontal(id="arg_get_row"):
                with Horizontal(id="args_container"):
                    pass
                yield Button("Get", id="btn_get", variant="primary", disabled=True)
            yield Label("", id="status_label")
            yield TextArea("", id="result_text", language="json", read_only=True)
            with Horizontal(id="action_row"):
                yield Button("Clear", id="btn_clear", variant="default")
                yield Button("Next »", id="btn_next", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#status_label").display = False
        self.query_one("#btn_clear").display = False
        self.query_one("#btn_next").display = False

    async def on_show(self) -> None:
        state = await self.app.service.active_state()  # type: ignore[attr-defined]
        if self._last_state is None:
            self._last_state = state
            return
        changed = (
            state.config_path != self._last_state.config_path
            or state.group_name != self._last_state.group_name
            or state.profile_name != self._last_state.profile_name
        )
        self._last_state = state
        if changed:
            await self._full_reset()

    async def _full_reset(self) -> None:
        self._current_cmd = None
        self._cursor = None
        self.query_one("#cmd_select", Select).clear()
        await self.query_one("#args_container").remove_children()
        self.query_one("#result_text", TextArea).load_text("")
        self.query_one("#btn_get").disabled = True
        self.query_one("#btn_clear").display = False
        self.query_one("#btn_next").display = False
        self._hide_status()

    def notify_state_changed(self, new_state: ActiveState) -> None:
        if self._last_state is not None and (
            new_state.config_path != self._last_state.config_path
            or new_state.group_name != self._last_state.group_name
            or new_state.profile_name != self._last_state.profile_name
        ):
            self.run_worker(self._full_reset(), exclusive=True, group="reset")
        self._last_state = new_state

    def _show_status(self, text: str, variant: str = "success") -> None:
        lbl = self.query_one("#status_label", Label)
        lbl.update(text)
        lbl.remove_class("error")
        lbl.remove_class("success")
        if variant == "error":
            lbl.add_class("error")
        lbl.display = True

    def _hide_status(self) -> None:
        self.query_one("#status_label").display = False

    @on(Select.Changed, "#cmd_select")
    def on_command_selected(self, event: Select.Changed) -> None:
        if event.value is Select.BLANK:
            self._current_cmd = None
            self.query_one("#btn_get").disabled = True
            return
        self._current_cmd = str(event.value)
        self._cursor = None
        self._hide_status()
        self.run_worker(
            self._render_and_load(str(event.value)),
            exclusive=True,
            group="render",
        )

    async def _render_and_load(self, cmd_name: str) -> None:
        cmd_info = COMMAND_LOOKUP.get(cmd_name)
        if cmd_info is None:
            return
        container = self.query_one("#args_container")
        await container.remove_children()
        if cmd_info.args:
            widgets = [_make_arg_widget(a) for a in cmd_info.args]
            await container.mount(*widgets)
        self.query_one("#btn_get").disabled = False
        self.query_one("#btn_clear").display = False
        self.query_one("#btn_next").display = False
        await self._load_pickers(cmd_info)

    async def _load_pickers(self, cmd_info: CommandInfo) -> None:
        state = await self.app.service.active_state()  # type: ignore[attr-defined]

        if _has_owner_arg(cmd_info):
            addresses = await self.app.service.list_addresses(state.group_name or "")  # type: ignore[attr-defined]
            for w in self.query_one("#args_container").children:
                if isinstance(w, AddressSelect):
                    w._addresses = addresses
                    opts = [(f"{a.alias} ({a.address[:8]}…)", a.address) for a in addresses]
                    opts.append(("Other…", "__other__"))
                    w.query_one(Select).set_options(opts)
                    if addresses:
                        w.query_one(Select).value = addresses[0].address

        if _needs_objects(cmd_info):
            owner = state.address
            if owner:
                objects = await self.app.service.get_owned_objects(owner)  # type: ignore[attr-defined]
                for w in self.query_one("#args_container").children:
                    if isinstance(w, (ObjectSelect, ObjectChecklist, ForVersionsWidget)):
                        w.populate(objects)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        btn_id = event.button.id
        if btn_id == "btn_get":
            self._on_get()
        elif btn_id == "btn_next":
            self._on_next()
        elif btn_id == "btn_clear":
            self._on_clear()

    def _on_get(self) -> None:
        if not self._current_cmd:
            return
        errors, kwargs = self._collect_args()
        if errors:
            self._show_status("✗ " + "; ".join(errors), "error")
            return
        self._cursor = None
        self._hide_status()
        self.run_worker(
            self._execute(self._current_cmd, kwargs, None),
            exclusive=True,
            group="execute",
        )

    def _on_next(self) -> None:
        if not self._current_cmd or self._cursor is None:
            return
        _, kwargs = self._collect_args()
        self.run_worker(
            self._execute(self._current_cmd, kwargs, self._cursor),
            exclusive=True,
            group="execute",
        )

    def _on_clear(self) -> None:
        self.query_one("#result_text", TextArea).load_text("")
        self._cursor = None
        self.query_one("#btn_clear").display = False
        self.query_one("#btn_next").display = False
        self._hide_status()

    def _collect_args(self) -> tuple[list[str], dict]:
        errors: list[str] = []
        kwargs: dict = {}
        for w in self.query_one("#args_container").children:
            if isinstance(w, (PlainInput, MultiValueInput, AddressSelect,
                               ObjectSelect, ObjectChecklist, ForVersionsWidget)):
                err = w.validate()
                if err:
                    errors.append(err)
                else:
                    name, value = w.get_name_value()
                    if value is not None:
                        kwargs[name] = value
        return errors, kwargs

    async def _execute(self, cmd_name: str, kwargs: dict, cursor: bytes | None) -> None:
        result: ReadResult = await self.app.service.execute_read(  # type: ignore[attr-defined]
            cmd_name, kwargs, cursor
        )
        if result.error:
            self._show_status(f"✗ {result.error}", "error")
            self.query_one("#result_text", TextArea).load_text("")
            self.query_one("#btn_clear").display = False
            self.query_one("#btn_next").display = False
        else:
            self._cursor = result.cursor
            text = result.json_str or ""
            self.query_one("#result_text", TextArea).load_text(text)
            self.query_one("#btn_clear").display = bool(text)
            cmd_info = COMMAND_LOOKUP.get(cmd_name)
            is_pageable = cmd_info is not None and cmd_info.pageable
            if is_pageable and result.cursor:
                self.query_one("#btn_next").display = True
                self.query_one("#btn_next").disabled = False
            else:
                self.query_one("#btn_next").display = False
            lines = text.count("\n") + 1 if text else 0
            self._show_status(f"✓ {lines} lines returned", "success")
