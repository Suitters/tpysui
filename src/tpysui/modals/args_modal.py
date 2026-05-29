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

_TXN_ARG_NAMES = frozenset({"gas_mode", "gas", "budget"})

# Sources whose values represent unique on-chain identifiers — duplicates are rejected.
_UNIQUE_SOURCES = frozenset({"owned_coins", "owned_objects", "group_addresses"})


def _widget_category(arg: ArgSpec) -> str:
    if arg.multiple:
        return "multiple"
    if arg.source == "group_addresses":
        return "address_select"
    if arg.source in ("owned_coins", "owned_objects", "owned_object_types") or arg.default:
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
        self._options: list[tuple[str, str]] = []
        self._field_options: dict[str, list[tuple[str, str]]] = {}

    def set_options(self, options: list[tuple[str, str]]) -> None:
        self._options = options

    def set_field_options(self, field_options: dict[str, list[tuple[str, str]]]) -> None:
        self._field_options = field_options

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
            self.app.push_screen(
                CollectorModal(
                    self._arg,
                    list(self._entries),
                    options=self._options,
                    field_options=self._field_options,
                ),
                on_result,
            )

    def get_value(self) -> list | None:
        return self._entries if self._entries else None


class CollectorModal(ModalScreen[list | None]):
    """Sub-modal for collecting a list of values for a multiple=true arg."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", priority=True)]

    def __init__(
        self,
        arg: ArgSpec,
        entries: list,
        options: list[tuple[str, str]] | None = None,
        field_options: dict[str, list[tuple[str, str]]] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._arg = arg
        self._entries: list = list(entries)
        self._options: list[tuple[str, str]] = options or []
        self._field_options: dict[str, list[tuple[str, str]]] = field_options or {}
        self._editing_row: int | None = None

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
                yield Label("─ Add entry ─", classes="staging_label", id="staging_title_lbl")
                yield Label("", id="staging_error_lbl", classes="staging_error_lbl")
                if self._is_compound:
                    for field in self._fields:
                        field_opts = self._field_options.get(field.name, [])
                        with Horizontal(classes="staging_row"):
                            yield Label(f"{field.name}:")
                            if field_opts:
                                with Vertical(classes="staging_field_col"):
                                    yield Select(
                                        field_opts + [("Other…", _OTHER)],
                                        id=f"staging_{field.name}_sel",
                                        allow_blank=False,
                                    )
                                    yield Input(
                                        id=f"staging_{field.name}_other",
                                        placeholder=field.kind.validation or "value",
                                        classes="staging_other_inp",
                                    )
                            else:
                                yield Input(
                                    id=f"staging_{field.name}",
                                    placeholder=field.kind.validation or "value",
                                )
                else:
                    with Horizontal(classes="staging_row"):
                        yield Label(f"{self._arg.name}:")
                        if self._options:
                            with Vertical(classes="staging_field_col"):
                                yield Select(
                                    self._options + [("Other…", _OTHER)],
                                    id="staging_sel",
                                    allow_blank=False,
                                )
                                yield Input(
                                    id="staging_other",
                                    placeholder=self._arg.kind.validation or "value",
                                    classes="staging_other_inp",
                                )
                        else:
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
        for inp in self.query(".staging_other_inp"):
            inp.display = False
        self.query_one("#staging_error_lbl", Label).display = False

    def _setup_columns(self, table: DataTable) -> None:
        table.add_column("#", key="idx", width=4)
        if self._is_compound:
            for field in self._fields:
                table.add_column(field.name, key=field.name)
        else:
            table.add_column("value", key="value")

    def _display_value(self, raw: str) -> str:
        """Resolve a raw value to its display label using the options list."""
        for label, val in self._options:
            if val == raw:
                return label
        return raw

    def _display_field_value(self, field_name: str, raw: str) -> str:
        """Resolve a compound field's raw value to its display label."""
        for label, val in self._field_options.get(field_name, []):
            if val == raw:
                return label
        return str(raw)

    def _append_row(self, table: DataTable, entry: Any) -> None:
        idx = str(table.row_count + 1)
        if self._is_compound:
            row = [idx] + [
                self._display_field_value(f.name, str(entry.get(f.name, "")))
                for f in self._fields
            ]
        else:
            row = [idx, self._display_value(str(entry))]
        table.add_row(*row)

    def _rebuild_table(self, table: DataTable) -> None:
        table.clear()
        for entry in self._entries:
            self._append_row(table, entry)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        row_idx = event.cursor_row
        if 0 <= row_idx < len(self._entries):
            self._editing_row = row_idx
            self._populate_staging(self._entries[row_idx])
            self.query_one("#btn_add", Button).label = "Update"
            self.query_one("#staging_title_lbl", Label).update("─ Edit entry ─")

    def on_select_changed(self, event: Select.Changed) -> None:
        sel_id = event.select.id or ""
        if sel_id == "staging_sel":
            try:
                self.query_one("#staging_other", Input).display = (event.value == _OTHER)
            except Exception:
                pass
        elif sel_id.endswith("_sel") and sel_id.startswith("staging_"):
            field_name = sel_id[len("staging_"):-len("_sel")]
            try:
                self.query_one(f"#staging_{field_name}_other", Input).display = (
                    event.value == _OTHER
                )
            except Exception:
                pass

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

    def _get_staging_field_value(self, field_name: str) -> str | None:
        if field_name in self._field_options:
            try:
                sel = self.query_one(f"#staging_{field_name}_sel", Select)
                if sel.value == _OTHER:
                    return (
                        self.query_one(f"#staging_{field_name}_other", Input).value.strip()
                        or None
                    )
                if sel.value is not Select.BLANK:
                    return str(sel.value)
                return None
            except Exception:
                return None
        else:
            try:
                return self.query_one(f"#staging_{field_name}", Input).value.strip() or None
            except Exception:
                return None

    def _get_staging_simple_value(self) -> str | None:
        if self._options:
            try:
                sel = self.query_one("#staging_sel", Select)
                if sel.value == _OTHER:
                    return self.query_one("#staging_other", Input).value.strip() or None
                if sel.value is not Select.BLANK:
                    return str(sel.value)
                return None
            except Exception:
                return None
        else:
            try:
                return self.query_one("#staging_value", Input).value.strip() or None
            except Exception:
                return None

    def _read_staging(self) -> Any | None:
        if self._is_compound:
            entry: dict[str, Any] = {}
            for field in self._fields:
                v = self._get_staging_field_value(field.name)
                if v is None and not field.optional:
                    return None
                if v is not None:
                    if field.kind.validation == "unsigned_int":
                        try:
                            entry[field.name] = int(v)
                        except ValueError:
                            return None
                    else:
                        entry[field.name] = v
            return entry if entry else None
        else:
            return self._get_staging_simple_value()

    def _populate_staging(self, entry: Any) -> None:
        if self._is_compound:
            for field in self._fields:
                v = str(entry.get(field.name, ""))
                if field.name in self._field_options:
                    values = {val for _, val in self._field_options[field.name]}
                    try:
                        sel = self.query_one(f"#staging_{field.name}_sel", Select)
                        other_inp = self.query_one(f"#staging_{field.name}_other", Input)
                        if v in values:
                            sel.value = v
                            other_inp.display = False
                        else:
                            sel.value = _OTHER
                            other_inp.value = v
                            other_inp.display = True
                    except Exception:
                        pass
                else:
                    try:
                        self.query_one(f"#staging_{field.name}", Input).value = v
                    except Exception:
                        pass
        else:
            v = str(entry)
            if self._options:
                values = {val for _, val in self._options}
                try:
                    sel = self.query_one("#staging_sel", Select)
                    other_inp = self.query_one("#staging_other", Input)
                    if v in values:
                        sel.value = v
                        other_inp.display = False
                    else:
                        sel.value = _OTHER
                        other_inp.value = v
                        other_inp.display = True
                except Exception:
                    pass
            else:
                try:
                    self.query_one("#staging_value", Input).value = v
                except Exception:
                    pass

    def _clear_staging(self) -> None:
        self._editing_row = None
        self.query_one("#btn_add", Button).label = "Add"
        self.query_one("#staging_title_lbl", Label).update("─ Add entry ─")
        try:
            self.query_one("#staging_error_lbl", Label).display = False
        except Exception:
            pass
        if self._is_compound:
            for field in self._fields:
                if field.name in self._field_options:
                    try:
                        sel = self.query_one(f"#staging_{field.name}_sel", Select)
                        opts = self._field_options[field.name]
                        if opts:
                            sel.value = opts[0][1]
                        self.query_one(f"#staging_{field.name}_other", Input).value = ""
                        self.query_one(f"#staging_{field.name}_other", Input).display = False
                    except Exception:
                        pass
                else:
                    try:
                        self.query_one(f"#staging_{field.name}", Input).value = ""
                    except Exception:
                        pass
        else:
            if self._options:
                try:
                    sel = self.query_one("#staging_sel", Select)
                    if self._options:
                        sel.value = self._options[0][1]
                    self.query_one("#staging_other", Input).value = ""
                    self.query_one("#staging_other", Input).display = False
                except Exception:
                    pass
            else:
                try:
                    self.query_one("#staging_value", Input).value = ""
                except Exception:
                    pass

    def _on_add(self) -> None:
        table = self.query_one("#entries_table", DataTable)
        err_lbl = self.query_one("#staging_error_lbl", Label)
        entry = self._read_staging()
        if entry is None:
            return
        if (
            not self._is_compound
            and self._arg.source in _UNIQUE_SOURCES
            and entry in self._entries
        ):
            editing_same = (
                self._editing_row is not None
                and self._entries[self._editing_row] == entry
            )
            if not editing_same:
                err_lbl.update("Already in list")
                err_lbl.display = True
                return
        err_lbl.display = False
        if self._editing_row is not None:
            self._entries[self._editing_row] = entry
            self._rebuild_table(table)
        else:
            self._entries.append(entry)
            self._append_row(table, entry)
        self._clear_staging()

    def _on_remove(self) -> None:
        table = self.query_one("#entries_table", DataTable)
        if not self._entries:
            return
        cursor = table.cursor_row
        if 0 <= cursor < len(self._entries):
            self._entries.pop(cursor)
            self._rebuild_table(table)
        self._clear_staging()

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
        is_write = self._entry.mode == "write"
        with Vertical(id="args_dialog"):
            yield Label(self._entry.name, id="modal_title")
            with VerticalScroll(id="args_scroll"):
                if is_write:
                    util_args = [a for a in self._entry.args if a.name not in _TXN_ARG_NAMES]
                    txn_args = [a for a in self._entry.args if a.name in _TXN_ARG_NAMES]
                    yield Label("── Utility Args ──", classes="args_section_label")
                    for arg in util_args:
                        iv = self._values.get(arg.name)
                        yield self._build_widget(arg, iv)
                    if txn_args:
                        yield Label("── Transaction Args ──", classes="args_section_label")
                        for arg in txn_args:
                            iv = self._values.get(arg.name)
                            yield self._build_widget(arg, iv)
                else:
                    for arg in self._entry.args:
                        iv = self._values.get(arg.name)
                        yield self._build_widget(arg, iv)
            with Horizontal(id="modal_buttons"):
                yield Button("Cancel", id="btn_cancel", variant="default")
                yield Button("Ok", id="btn_ok", variant="primary")

    async def on_mount(self) -> None:
        self.run_worker(self._load_dynamic(), exclusive=False, group="args_load")
        if self._entry.mode == "write":
            self._sync_gas_availability()

    def on_select_changed(self, event: Select.Changed) -> None:
        if self._entry.mode != "write":
            return
        grandparent = getattr(getattr(event.select, "parent", None), "parent", None)
        if grandparent is None:
            return
        try:
            gas_mode_w = self.query_one("#arg_gas_mode", DefaultSelect)
            if grandparent is gas_mode_w:
                self._sync_gas_availability()
                return
        except Exception:
            pass
        try:
            owner_w = self.query_one("#arg_owner", AddressSelect)
            if grandparent is owner_w:
                _, addr = owner_w.get_name_value()
                if addr and addr != _OTHER:
                    self.run_worker(
                        self._reload_coins_for_owner(addr),
                        exclusive=True,
                        group="owner_reload",
                    )
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed) -> None:
        if self._entry.name != "splay-coins":
            return
        grandparent = getattr(getattr(event.input, "parent", None), "parent", None)
        if getattr(grandparent, "id", "") == "arg_number":
            has_number = bool(event.value.strip())
            try:
                recipients_w = self.query_one("#multi_recipients", MultipleRow)
                recipients_w.display = not has_number
                if has_number:
                    recipients_w._entries = []
                    recipients_w.query_one("#count_lbl", Label).update("0 entries")
            except Exception:
                pass

    def _sync_gas_availability(self) -> None:
        try:
            gas_mode_w = self.query_one("#arg_gas_mode", DefaultSelect)
            val = gas_mode_w.get_value()
            show_gas = val == "Use Gas Coin"
        except Exception:
            show_gas = True
        try:
            gas_w = self.query_one("#multi_gas", MultipleRow)
            gas_w.display = show_gas
        except Exception:
            pass

    async def _reload_coins_for_owner(self, owner: str) -> None:
        try:
            coins = await self.app.service.get_owned_coins(owner)  # type: ignore[attr-defined]
        except Exception:
            return
        coin_extra = [
            (f"{fmt_id(c.object_id)} — {c.object_type[:24]}", c.object_id)
            for c in coins
        ]
        for arg in self._entry.args:
            if arg.source != "owned_coins":
                continue
            if not arg.multiple:
                try:
                    w = self.query_one(f"#arg_{arg.name}", DefaultSelect)
                    w.populate_extra(coin_extra)
                except Exception:
                    pass
            else:
                try:
                    w = self.query_one(f"#multi_{arg.name}", MultipleRow)
                    w.set_options(coin_extra)
                except Exception:
                    pass

    async def _load_dynamic(self) -> None:
        state = await self.app.service.active_state()  # type: ignore[attr-defined]

        effective_address = state.address
        if self._entry.mode == "write":
            owner_initial = self._values.get("owner")
            if owner_initial and isinstance(owner_initial, str):
                effective_address = owner_initial

        query_address = effective_address if self._entry.mode == "write" else state.address

        def _needs_source(src: str) -> bool:
            for a in self._entry.args:
                if a.source == src:
                    return True
                for f in (a.kind.fields or ()):
                    if getattr(f, "source", None) == src:
                        return True
            return False

        addr_extra: list[tuple[str, str]] = []
        coin_extra: list[tuple[str, str]] = []
        obj_extra: list[tuple[str, str]] = []

        if _needs_source("group_addresses"):
            addresses = await self.app.service.list_addresses(  # type: ignore[attr-defined]
                state.group_name or ""
            )
            addr_extra = [(f"{a.alias} ({fmt_id(a.address)})", a.address) for a in addresses]
            opts = list(addr_extra) + [("Other…", _OTHER)]
            addr_args = [a for a in self._entry.args if a.source == "group_addresses" and not a.multiple]
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
                elif effective_address and any(a.address == effective_address for a in addresses):
                    sel.value = effective_address
                elif state.address and any(a.address == state.address for a in addresses):
                    sel.value = state.address
                elif addresses:
                    sel.value = addresses[0].address
            addr_multi_args = [a for a in self._entry.args if a.source == "group_addresses" and a.multiple]
            for arg in addr_multi_args:
                try:
                    w = self.query_one(f"#multi_{arg.name}", MultipleRow)
                    w.set_options(addr_extra)
                except Exception:
                    pass
        else:
            addresses = []

        coins = []
        if _needs_source("owned_coins") and query_address:
            coins = await self.app.service.get_owned_coins(query_address)  # type: ignore[attr-defined]
            coin_extra = [
                (f"{fmt_id(c.object_id)} — {c.object_type[:24]}", c.object_id)
                for c in coins
            ]
            coin_single_args = [
                a for a in self._entry.args if a.source == "owned_coins" and not a.multiple
            ]
            for arg in coin_single_args:
                try:
                    w = self.query_one(f"#arg_{arg.name}", DefaultSelect)
                except Exception:
                    continue
                if arg.kind.validation == "sui_address":
                    w.populate_extra(coin_extra)
                else:
                    seen: set[str] = set()
                    type_extra: list[tuple[str, str]] = []
                    for c in coins:
                        if c.object_type not in seen:
                            seen.add(c.object_type)
                            type_extra.append((c.object_type, c.object_type))
                    w.populate_extra(type_extra)
            coin_multi_args = [
                a for a in self._entry.args if a.source == "owned_coins" and a.multiple
            ]
            for arg in coin_multi_args:
                try:
                    w = self.query_one(f"#multi_{arg.name}", MultipleRow)
                    w.set_options(coin_extra)
                except Exception:
                    pass

        objects = []
        if _needs_source("owned_objects") and query_address:
            objects = await self.app.service.get_owned_objects(query_address)  # type: ignore[attr-defined]
            obj_extra = [
                (f"{fmt_id(o.object_id)} — {o.object_type[:24]}", o.object_id)
                for o in objects
            ]
            obj_single_args = [
                a for a in self._entry.args if a.source == "owned_objects" and not a.multiple
            ]
            for arg in obj_single_args:
                try:
                    w = self.query_one(f"#arg_{arg.name}", DefaultSelect)
                    w.populate_extra(obj_extra)
                except Exception:
                    pass
            obj_multi_args = [
                a for a in self._entry.args if a.source == "owned_objects" and a.multiple
            ]
            for arg in obj_multi_args:
                try:
                    w = self.query_one(f"#multi_{arg.name}", MultipleRow)
                    w.set_options(obj_extra)
                except Exception:
                    pass

        if _needs_source("owned_object_types") and query_address:
            if not objects:
                objects = await self.app.service.get_owned_objects(query_address)  # type: ignore[attr-defined]
            types = list(dict.fromkeys(o.object_type for o in objects if o.object_type))
            type_vals = [(t, t) for t in types]
            for arg in self._entry.args:
                if arg.source == "owned_object_types" and not arg.multiple:
                    try:
                        w = self.query_one(f"#arg_{arg.name}", DefaultSelect)
                        w.populate_extra(type_vals)
                    except Exception:
                        pass

        compound_multi_args = [
            a for a in self._entry.args
            if a.multiple and a.kind.type == "compound" and a.kind.fields
        ]
        for arg in compound_multi_args:
            field_opts: dict[str, list[tuple[str, str]]] = {}
            for field in (arg.kind.fields or ()):
                fsrc = getattr(field, "source", None)
                if fsrc == "owned_coins" and coin_extra:
                    field_opts[field.name] = coin_extra
                elif fsrc == "group_addresses" and addr_extra:
                    field_opts[field.name] = addr_extra
                elif fsrc == "owned_objects" and obj_extra:
                    field_opts[field.name] = obj_extra
            if field_opts:
                try:
                    w = self.query_one(f"#multi_{arg.name}", MultipleRow)
                    w.set_field_options(field_opts)
                except Exception:
                    pass

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
                show_other=(arg.source != "none"),
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
