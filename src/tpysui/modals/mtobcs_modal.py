#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""MtobcsModal — edit UI for move-struct-to-bcs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Input, Label, Select

from ..modals.save_modal import SaveModal


_STRUCT_TYPES = [("Structure", "Structure"), ("GenericStructure", "GenericStructure")]


class MtobcsModal(ModalScreen[dict | None]):
    """Edit move-struct-to-bcs targets directive."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", priority=True)]

    def __init__(self, initial_values: dict | None = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._targets: list[dict] = []
        self._params: list[tuple[str, str]] = []
        self._editing_target: int | None = None
        self._editing_param: int | None = None
        if initial_values:
            self._targets = list(initial_values.get("targets", []))
            self._config_path = initial_values.get("directive_file", "") or ""
            self._dirty = initial_values.get("_dirty", True)
        else:
            self._config_path = ""
            self._dirty = True

    def compose(self) -> ComposeResult:
        with Vertical(id="mtobcs_dialog"):
            yield Label("move-struct-to-bcs", id="mtobcs_title")

            with Horizontal(id="mtobcs_config_row"):
                yield Label("Config File:")
                yield Input(
                    id="config_path_inp",
                    value=self._config_path,
                    placeholder="(unsaved)",
                )
                yield Button("Save", id="btn_save_config", variant="error")

            yield Label(
                "Targets (add from ── Entry ── below)",
                classes="mtobcs_section_label",
            )
            yield DataTable(id="targets_table", show_cursor=True, cursor_type="row")

            with Vertical(id="mtobcs_staging"):
                yield Label("── Entry ──", classes="mtobcs_staging_title")
                with Horizontal(classes="mtobcs_staging_row"):
                    yield Label("Type:")
                    yield Select(_STRUCT_TYPES, id="staging_type", allow_blank=False)
                with Horizontal(classes="mtobcs_staging_row"):
                    yield Label("Move Structure:")
                    yield Input(id="staging_value", placeholder="addr::module::Type")
                with Horizontal(classes="mtobcs_staging_row"):
                    yield Label("Out file:")
                    yield Input(id="staging_outfile", placeholder="/full/path/to/output.py")
                    yield Button("…", id="btn_browse_outfile", variant="default")

                with Vertical(id="mtobcs_generic_params"):
                    yield Label(
                        "── Generic params (name: type) ──",
                        classes="mtobcs_staging_title",
                    )
                    yield DataTable(id="params_table", show_cursor=True)
                    with Horizontal(classes="mtobcs_staging_row"):
                        yield Input(id="param_name_inp", placeholder="param name")
                        yield Input(id="param_value_inp", placeholder="type value")
                    with Horizontal(id="mtobcs_param_buttons"):
                        yield Button("Add", id="btn_add_param", variant="primary")
                        yield Button("Update", id="btn_update_param", variant="primary", disabled=True)
                        yield Button("Delete", id="btn_remove_param", variant="error")

                with Horizontal(id="mtobcs_entry_buttons"):
                    yield Button("Add Target", id="btn_add_target", variant="primary")
                    yield Button("Update", id="btn_update_target", variant="primary", disabled=True)
                    yield Button("Remove", id="btn_remove_target", variant="error")

            with Horizontal(id="mtobcs_action_buttons"):
                yield Button("Cancel", id="btn_cancel", variant="default")
                yield Button("OK", id="btn_ok", variant="success")

    def on_mount(self) -> None:
        t = self.query_one("#targets_table", DataTable)
        t.add_columns("Type", "Move Struct", "Out file")
        p = self.query_one("#params_table", DataTable)
        p.add_columns("Param name", "Type value")
        for entry in self._targets:
            self._append_target_row(entry)
        self.query_one("#mtobcs_generic_params").display = False
        self._refresh_save_button()
        self.call_after_refresh(lambda: self.query_one("#staging_type", Select).focus())

    def _refresh_save_button(self) -> None:
        btn = self.query_one("#btn_save_config", Button)
        btn.variant = "error" if (self._dirty or not self._config_path) else "success"

    def _mark_dirty(self) -> None:
        self._dirty = True
        self._refresh_save_button()

    @on(Select.Changed, "#staging_type")
    def _on_type_changed(self, event: Select.Changed) -> None:
        self.query_one("#mtobcs_generic_params").display = (event.value == "GenericStructure")

    def _load_target_into_staging(self, row_idx: int) -> None:
        if row_idx < 0 or row_idx >= len(self._targets):
            return
        self._editing_target = row_idx
        entry = self._targets[row_idx]
        self.query_one("#staging_type", Select).value = entry.get("type", "Structure")
        self.query_one("#staging_value", Input).value = entry.get("value", "")
        self.query_one("#staging_outfile", Input).value = entry.get("out_file", "")
        self._params = [
            (k, v) for k, v in entry.items() if k not in ("type", "value", "out_file")
        ]
        self._refresh_params_table()
        self.query_one("#btn_add_target", Button).disabled = True
        self.query_one("#btn_update_target", Button).disabled = False

    @on(DataTable.RowHighlighted, "#targets_table")
    def _on_target_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self._load_target_into_staging(event.cursor_row)

    @on(DataTable.RowSelected, "#targets_table")
    def _on_target_selected(self, event: DataTable.RowSelected) -> None:
        self._load_target_into_staging(event.cursor_row)

    @on(DataTable.RowSelected, "#params_table")
    def _on_param_selected(self, event: DataTable.RowSelected) -> None:
        row_idx = event.cursor_row
        if row_idx < 0 or row_idx >= len(self._params):
            return
        self._editing_param = row_idx
        k, v = self._params[row_idx]
        self.query_one("#param_name_inp", Input).value = k
        self.query_one("#param_value_inp", Input).value = v
        self.query_one("#btn_add_param", Button).disabled = True
        self.query_one("#btn_update_param", Button).disabled = False

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn_save_config":
            self._save_config()
        elif bid == "btn_browse_outfile":
            self._browse_out_file()
        elif bid == "btn_add_param":
            self._add_param()
        elif bid == "btn_update_param":
            self._update_param()
        elif bid == "btn_remove_param":
            self._remove_param()
        elif bid == "btn_add_target":
            self._add_target()
        elif bid == "btn_update_target":
            self._update_target()
        elif bid == "btn_remove_target":
            self._remove_target()
        elif bid == "btn_cancel":
            self.dismiss(None)
        elif bid == "btn_ok":
            self._ok()

    def _save_config(self) -> None:
        data = {"targets": self._targets}

        def do_save(path: Path) -> None:
            try:
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                self._config_path = str(path)
                self.query_one("#config_path_inp", Input).value = self._config_path
                self._dirty = False
                self._refresh_save_button()
            except OSError:
                pass

        if self._config_path:
            do_save(Path(self._config_path))
        else:
            def on_result(path: Path | None) -> None:
                if path:
                    do_save(path)
            self.app.push_screen(SaveModal(), on_result)

    def _browse_out_file(self) -> None:
        def on_result(path: Path | None) -> None:
            if path:
                p = path if path.suffix == ".py" else path.with_suffix(".py")
                self.query_one("#staging_outfile", Input).value = str(p)
        self.app.push_screen(SaveModal(default_filename="output.py"), on_result)

    def _add_param(self) -> None:
        name = self.query_one("#param_name_inp", Input).value.strip()
        value = self.query_one("#param_value_inp", Input).value.strip()
        if not name or not value:
            return
        self._params.append((name, value))
        self._refresh_params_table()
        self._clear_param_inputs()
        self._mark_dirty()

    def _update_param(self) -> None:
        if self._editing_param is None:
            return
        name = self.query_one("#param_name_inp", Input).value.strip()
        value = self.query_one("#param_value_inp", Input).value.strip()
        if not name or not value:
            return
        self._params[self._editing_param] = (name, value)
        self._editing_param = None
        self._refresh_params_table()
        self._clear_param_inputs()
        self.query_one("#btn_add_param", Button).disabled = False
        self.query_one("#btn_update_param", Button).disabled = True
        self._mark_dirty()

    def _remove_param(self) -> None:
        p = self.query_one("#params_table", DataTable)
        row_idx = p.cursor_row
        if 0 <= row_idx < len(self._params):
            self._params.pop(row_idx)
            self._editing_param = None
            self._refresh_params_table()
            self._clear_param_inputs()
            self.query_one("#btn_add_param", Button).disabled = False
            self.query_one("#btn_update_param", Button).disabled = True
            self._mark_dirty()

    def _refresh_params_table(self) -> None:
        p = self.query_one("#params_table", DataTable)
        p.clear()
        for k, v in self._params:
            p.add_row(k, v)

    def _clear_param_inputs(self) -> None:
        self.query_one("#param_name_inp", Input).value = ""
        self.query_one("#param_value_inp", Input).value = ""

    def _add_target(self) -> None:
        t_type = str(self.query_one("#staging_type", Select).value)
        if t_type == "GenericStructure" and not self._params:
            self.app.notify("GenericStructure requires at least one generic param.", severity="error")
            return
        entry = self._build_staging_entry()
        if entry is None:
            self.app.notify("Move Structure and Out file are required.", severity="warning")
            return
        out_file = entry.get("out_file", "")
        if any(t.get("out_file") == out_file for t in self._targets):
            self.app.notify("Out file path already used by another target.", severity="error")
            return
        self._targets.append(entry)
        self._append_target_row(entry)
        self._clear_staging()
        self._mark_dirty()

    def _update_target(self) -> None:
        if self._editing_target is None:
            return
        t_type = str(self.query_one("#staging_type", Select).value)
        if t_type == "GenericStructure" and not self._params:
            self.app.notify("GenericStructure requires at least one generic param.", severity="error")
            return
        entry = self._build_staging_entry()
        if entry is None:
            return
        out_file = entry.get("out_file", "")
        if any(
            i != self._editing_target and t.get("out_file") == out_file
            for i, t in enumerate(self._targets)
        ):
            self.app.notify("Out file path already used by another target.", severity="error")
            return
        self._targets[self._editing_target] = entry
        self._editing_target = None
        self._refresh_targets_table()
        self._clear_staging()
        self.query_one("#btn_add_target", Button).disabled = False
        self.query_one("#btn_update_target", Button).disabled = True
        self._mark_dirty()

    def _remove_target(self) -> None:
        t = self.query_one("#targets_table", DataTable)
        row_idx = t.cursor_row
        if 0 <= row_idx < len(self._targets):
            self._targets.pop(row_idx)
            self._editing_target = None
            self._refresh_targets_table()
            self._clear_staging()
            self.query_one("#btn_add_target", Button).disabled = False
            self.query_one("#btn_update_target", Button).disabled = True
            self._mark_dirty()

    def _build_staging_entry(self) -> dict | None:
        t_type = str(self.query_one("#staging_type", Select).value)
        t_value = self.query_one("#staging_value", Input).value.strip()
        t_outfile = self.query_one("#staging_outfile", Input).value.strip()
        if not t_value or not t_outfile:
            return None
        entry: dict = {"type": t_type, "value": t_value, "out_file": t_outfile}
        if t_type == "GenericStructure":
            for k, v in self._params:
                entry[k] = v
        return entry

    def _append_target_row(self, entry: dict) -> None:
        t = self.query_one("#targets_table", DataTable)
        t.add_row(entry.get("type", ""), entry.get("value", ""), entry.get("out_file", ""))

    def _refresh_targets_table(self) -> None:
        t = self.query_one("#targets_table", DataTable)
        t.clear()
        for entry in self._targets:
            self._append_target_row(entry)

    def _clear_staging(self) -> None:
        self.query_one("#staging_type", Select).value = "Structure"
        self.query_one("#staging_value", Input).value = ""
        self.query_one("#staging_outfile", Input).value = ""
        self._params = []
        self._editing_param = None
        self._refresh_params_table()
        self._clear_param_inputs()

    def _ok(self) -> None:
        self.dismiss({
            "directive_file": self._config_path,
            "targets": self._targets,
            "_dirty": self._dirty,
        })

    def action_cancel(self) -> None:
        self.dismiss(None)
