#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0
# -*- coding: utf-8 -*-

"""ArgsModal and CollectorModal — dynamic arg collection for taxonomy commands."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import Button, DataTable, Input, Label, Select

from ..services.taxonomy_loader import ArgSpec, CommandEntry, NamedFieldSpec
from ..utils.validators import (
    valid_base58,
    valid_move_identifier,
    valid_sui_address,
    valid_type_tag,
    valid_unsigned_int,
)
from ..widgets.arg_widgets import (
    AddressSelect,
    BoolToggle,
    DefaultSelect,
    PlainInput,
    fmt_id,
)

_OTHER = "__other__"

_VALIDATOR_MAP: dict[str, Any] = {
    "sui_address": valid_sui_address,
    "type_tag": valid_type_tag,
    "move_identifier": valid_move_identifier,
    "base58": valid_base58,
    "unsigned_int": valid_unsigned_int,
}


def _widget_category(arg: ArgSpec) -> str:
    if arg.multiple:
        return "multiple"
    if arg.source == "group_addresses":
        return "address_select"
    if arg.source in ("owned_coins", "owned_object_types") or arg.default:
        return "default_select"
    if arg.kind.type == "scalar" and arg.kind.validation == "bool":
        return "bool_toggle"
    return "plain_input"


class MultipleRow(Widget):
    """Summary row for a multiple=true arg; opens CollectorModal on Edit."""

    def __init__(self, arg: ArgSpec, entries: list, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._arg = arg
        self._entries: list = list(entries)

    def compose(self) -> ComposeResult:
        label = f"* {self._arg.name}" if not self._arg.optional else self._arg.name
        count = len(self._entries)
        summary = f"{count} {'entry' if count == 1 else 'entries'}"
        with Horizontal():
            yield Label(f"{label}:")
            yield Label(summary, id="count_lbl")
            yield Button("Edit…", id="edit_btn", variant="warning")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "edit_btn":
            def on_result(result: list | None) -> None:
                if result is not None:
                    self._entries = result
                    count = len(result)
                    self.query_one("#count_lbl", Label).update(
                        f"{count} {'entry' if count == 1 else 'entries'}"
                    )
            self.app.push_screen(CollectorModal(self._arg, list(self._entries)), on_result)

    def get_value(self) -> list | None:
        return self._entries if self._entries else None


class CollectorModal(ModalScreen[list | None]):
    """Sub-modal for collecting a list of values for a multiple=true arg."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", priority=True)]

    def __init__(self, arg: ArgSpec, entries: list, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._arg = arg
        self._entries: list = list(entries)

    @property
    def _is_compound(self) -> bool:
        return self._arg.kind.type == "compound"

    @property
    def _fields(self) -> tuple[NamedFieldSpec, ...]:
        return self._arg.kind.fields or ()

    def compose(self) -> ComposeResult:
        with Vertical(id="collector_dialog"):
            yield Label(f"Edit: {self._arg.name}", id="collector_title")
            with VerticalScroll(id="entries_scroll"):
                yield DataTable(id="entries_table", cursor_type="row")
            with Vertical(id="staging_area"):
                yield Label("─ Add entry ─", classes="staging_label")
                if self._is_compound:
                    for field in self._fields:
                        with Horizontal(classes="staging_row"):
                            yield Label(f"{field.name}:")
                            yield Input(
                                id=f"staging_{field.name}",
                                placeholder=field.kind.validation or "value",
                            )
                else:
                    with Horizontal(classes="staging_row"):
                        yield Label(f"{self._arg.name}:")
                        yield Input(
                            id="staging_value",
                            placeholder=self._arg.kind.validation or "value",
                        )
                with Horizontal(id="collector_add_buttons"):
                    yield Button("Add", id="btn_add", variant="primary")
                    yield Button("Remove", id="btn_remove", variant="warning")
            with Horizontal(id="collector_buttons"):
                yield Button("Cancel", id="btn_cancel", variant="default")
                yield Button("Done", id="btn_done", variant="success")

    def on_mount(self) -> None:
        table = self.query_one("#entries_table", DataTable)
        self._setup_columns(table)
        for entry in self._entries:
            self._append_row(table, entry)

    def _setup_columns(self, table: DataTable) -> None:
        table.add_column("#", key="idx", width=4)
        if self._is_compound:
            for field in self._fields:
                table.add_column(field.name, key=field.name)
        else:
            table.add_column("value", key="value")

    def _append_row(self, table: DataTable, entry: Any) -> None:
        idx = str(table.row_count + 1)
        if self._is_compound:
            row = [idx] + [str(entry.get(f.name, "")) for f in self._fields]
        else:
            row = [idx, str(entry)]
        table.add_row(*row)

    def _rebuild_table(self, table: DataTable) -> None:
        table.clear()
        for entry in self._entries:
            self._append_row(table, entry)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn_add":
            self._on_add()
        elif bid == "btn_remove":
            self._on_remove()
        elif bid == "btn_done":
            self.dismiss(self._entries)
        elif bid == "btn_cancel":
            self.action_cancel()

    def _on_add(self) -> None:
        table = self.query_one("#entries_table", DataTable)
        if self._is_compound:
            entry: dict[str, Any] = {}
            for field in self._fields:
                inp = self.query_one(f"#staging_{field.name}", Input)
                v = inp.value.strip()
                if not v and not field.optional:
                    return
                if v:
                    if field.kind.validation == "unsigned_int":
                        try:
                            entry[field.name] = int(v)
                        except ValueError:
                            return
                    else:
                        entry[field.name] = v
            if not entry:
                return
            self._entries.append(entry)
            self._append_row(table, entry)
            for field in self._fields:
                self.query_one(f"#staging_{field.name}", Input).value = ""
        else:
            v = self.query_one("#staging_value", Input).value.strip()
            if not v:
                return
            self._entries.append(v)
            self._append_row(table, v)
            self.query_one("#staging_value", Input).value = ""

    def _on_remove(self) -> None:
        table = self.query_one("#entries_table", DataTable)
        if not self._entries:
            return
        cursor = table.cursor_row
        if 0 <= cursor < len(self._entries):
            self._entries.pop(cursor)
            self._rebuild_table(table)

    def key_escape(self) -> None:
        self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)


class ArgsModal(ModalScreen[dict[str, Any] | None]):
    """Dynamic arg-collection modal built from a CommandEntry spec."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", priority=True),
        ("ctrl+s", "action_ok", "Ok"),
    ]

    def __init__(
        self,
        entry: CommandEntry,
        values: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._entry = entry
        self._values: dict[str, Any] = values or {}

    def compose(self) -> ComposeResult:
        with Vertical(id="args_dialog"):
            yield Label(self._entry.name, id="modal_title")
            with VerticalScroll(id="args_scroll"):
                for arg in self._entry.args:
                    iv = self._values.get(arg.name)
                    yield self._build_widget(arg, iv)
            with Horizontal(id="modal_buttons"):
                yield Button("Cancel", id="btn_cancel", variant="default")
                yield Button("Ok", id="btn_ok", variant="primary")

    async def on_mount(self) -> None:
        self.run_worker(self._load_dynamic(), exclusive=False, group="args_load")

    async def _load_dynamic(self) -> None:
        state = await self.app.service.active_state()  # type: ignore[attr-defined]

        addr_args = [a for a in self._entry.args if a.source == "group_addresses"]
        if addr_args:
            addresses = await self.app.service.list_addresses(  # type: ignore[attr-defined]
                state.group_name or ""
            )
            opts = [(f"{a.alias} ({fmt_id(a.address)})", a.address) for a in addresses]
            opts.append(("Other…", _OTHER))
            for arg in addr_args:
                try:
                    w = self.query_one(f"#arg_{arg.name}", AddressSelect)
                except Exception:
                    continue
                w._addresses = addresses
                sel = w.query_one(Select)
                sel.set_options(opts)
                iv = self._values.get(arg.name, "")
                if iv and any(a.address == iv for a in addresses):
                    sel.value = iv
                elif state.address and any(a.address == state.address for a in addresses):
                    sel.value = state.address
                elif addresses:
                    sel.value = addresses[0].address

        coin_args = [a for a in self._entry.args if a.source == "owned_coins"]
        if coin_args and state.address:
            coins = await self.app.service.get_owned_coins(state.address)  # type: ignore[attr-defined]
            for arg in coin_args:
                try:
                    w = self.query_one(f"#arg_{arg.name}", DefaultSelect)
                except Exception:
                    continue
                if arg.kind.validation == "sui_address":
                    extra = [
                        (f"{fmt_id(c.object_id)} — {c.object_type[:24]}", c.object_id)
                        for c in coins
                    ]
                else:
                    seen: set[str] = set()
                    extra = []
                    for c in coins:
                        if c.object_type not in seen:
                            seen.add(c.object_type)
                            extra.append((c.object_type, c.object_type))
                w.populate_extra(extra)

        obj_args = [a for a in self._entry.args if a.source == "owned_objects" and not a.multiple]
        if obj_args and state.address:
            objects = await self.app.service.get_owned_objects(state.address)  # type: ignore[attr-defined]
            for arg in obj_args:
                try:
                    w = self.query_one(f"#arg_{arg.name}", DefaultSelect)
                except Exception:
                    continue
                extra = [
                    (f"{fmt_id(o.object_id)} — {o.object_type[:24]}", o.object_id)
                    for o in objects
                ]
                w.populate_extra(extra)

        type_args = [a for a in self._entry.args if a.source == "owned_object_types" and not a.multiple]
        if type_args and state.address:
            objects = await self.app.service.get_owned_objects(state.address)  # type: ignore[attr-defined]
            types = list(dict.fromkeys(o.object_type for o in objects if o.object_type))
            extra = [(t, t) for t in types]
            for arg in type_args:
                try:
                    w = self.query_one(f"#arg_{arg.name}", DefaultSelect)
                except Exception:
                    continue
                w.populate_extra(extra)

    def _build_widget(self, arg: ArgSpec, initial_value: Any) -> Widget:
        label = f"* {arg.name}" if not arg.optional else arg.name
        cat = _widget_category(arg)

        if cat == "multiple":
            entries = initial_value if isinstance(initial_value, list) else []
            return MultipleRow(arg=arg, entries=entries, id=f"multi_{arg.name}")

        if cat == "address_select":
            return AddressSelect(label=label, addresses=[], id=f"arg_{arg.name}")

        if cat == "default_select":
            static_defaults = [str(d) for d in arg.default]
            iv_str = str(initial_value) if initial_value is not None else ""
            return DefaultSelect(
                label=label,
                defaults=static_defaults,
                optional=arg.optional,
                initial_value=iv_str,
                id=f"arg_{arg.name}",
            )

        if cat == "bool_toggle":
            if initial_value is not None:
                iv_bool = bool(initial_value)
            elif arg.default:
                iv_bool = bool(arg.default[0])
            else:
                iv_bool = True
            return BoolToggle(
                label=label,
                optional=arg.optional,
                initial_value=iv_bool,
                id=f"arg_{arg.name}",
            )

        validator = _VALIDATOR_MAP.get(arg.kind.validation or "")
        iv_str = str(initial_value) if initial_value is not None else ""
        return PlainInput(
            label=label,
            validator=validator,
            optional=arg.optional,
            default=iv_str,
            id=f"arg_{arg.name}",
        )

    def _collect(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for arg in self._entry.args:
            cat = _widget_category(arg)
            try:
                if cat == "multiple":
                    w = self.query_one(f"#multi_{arg.name}", MultipleRow)
                    v = w.get_value()
                    if v is not None:
                        result[arg.name] = v
                elif cat == "address_select":
                    w = self.query_one(f"#arg_{arg.name}", AddressSelect)
                    _, v = w.get_name_value()
                    if v is not None:
                        result[arg.name] = v
                elif cat == "default_select":
                    w = self.query_one(f"#arg_{arg.name}", DefaultSelect)
                    v = w.get_value()
                    if v is not None:
                        result[arg.name] = v
                elif cat == "bool_toggle":
                    w = self.query_one(f"#arg_{arg.name}", BoolToggle)
                    result[arg.name] = w.get_value()
                else:
                    w = self.query_one(f"#arg_{arg.name}", PlainInput)
                    _, v = w.get_name_value()
                    if v is not None:
                        if arg.kind.validation == "unsigned_int":
                            result[arg.name] = int(v)
                        else:
                            result[arg.name] = v
            except Exception:
                pass
        return result

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn_ok":
            self.action_ok()
        elif bid == "btn_cancel":
            self.action_cancel()

    def key_escape(self) -> None:
        self.action_cancel()

    def action_ok(self) -> None:
        self.dismiss(self._collect())

    def action_cancel(self) -> None:
        self.dismiss(None)
