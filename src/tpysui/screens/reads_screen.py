#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Button, Label, Select, TextArea

from ..modals.args_modal import ArgsModal
from ..modals.save_modal import SaveModal
from ..services.base import ActiveState, ReadResult
from ..services.taxonomy_loader import CommandEntry


class ReadsScreen(Widget):
    """Area 2 — Blockchain Data Reads."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._current_cmd: str | None = None
        self._cursor: bytes | None = None
        self._last_state: ActiveState | None = None
        self._last_args_by_cmd: dict[str, dict[str, Any] | None] = {}
        self._cmds_populated: bool = False
        self._last_result_text: str = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="reads_body"):
            with Horizontal(id="cmd_row"):
                yield Select(
                    [],
                    id="cmd_select",
                    allow_blank=True,
                    prompt="Select a read command…",
                )
            yield Label("", id="cmd_desc_lbl", classes="cmd_desc_lbl")
            with Horizontal(id="action_row"):
                yield Button("Args...", id="btn_args", variant="primary", disabled=True)
                yield Label("", id="status_lbl")
                yield Button("Reset", id="btn_reset", variant="primary", disabled=True)
                yield Button("Run", id="btn_run", variant="primary", disabled=True)
            yield Label("", id="result_status_lbl")
            yield TextArea("", id="result_text", language="json", read_only=True)
            with Horizontal(id="export_row"):
                yield Button("Copy", id="btn_copy", variant="primary")
                yield Button("Save...", id="btn_save_file", variant="primary")
            with Horizontal(id="next_row"):
                yield Button("Clear", id="btn_clear", variant="primary")
                yield Button("Next »", id="btn_next", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#export_row").display = False
        self.query_one("#btn_clear").display = False
        self.query_one("#btn_next").display = False
        self.query_one("#result_status_lbl").display = False

    async def on_show(self) -> None:
        if not self._cmds_populated:
            options = [(name, name) for name in self.app.command_registry]  # type: ignore[attr-defined]
            self.query_one("#cmd_select", Select).set_options(options)
            self._cmds_populated = True

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

    def notify_state_changed(self, new_state: ActiveState) -> None:
        if self._last_state is not None and (
            new_state.config_path != self._last_state.config_path
            or new_state.group_name != self._last_state.group_name
            or new_state.profile_name != self._last_state.profile_name
        ):
            self.run_worker(self._full_reset(), exclusive=True, group="reset")
        self._last_state = new_state

    def _clear_result_area(self) -> None:
        self._last_result_text = ""
        self.query_one("#result_text", TextArea).load_text("")
        self.query_one("#export_row").display = False
        self.query_one("#btn_clear").display = False
        self.query_one("#btn_next").display = False
        self._clear_result_status()

    @on(Select.Changed, "#cmd_select")
    def on_command_selected(self, event: Select.Changed) -> None:
        self._clear_result_area()
        if event.value is Select.BLANK:
            self._current_cmd = None
            self._disable_actions()
            self.query_one("#cmd_desc_lbl", Label).update("")
            return
        cmd_name = str(event.value)
        self._current_cmd = cmd_name
        self._cursor = None
        entry: CommandEntry | None = self.app.command_registry.get(cmd_name)  # type: ignore[attr-defined]
        if entry is None:
            return
        self.query_one("#cmd_desc_lbl", Label).update(entry.description)
        if not entry.args:
            self._last_args_by_cmd.setdefault(cmd_name, {})
        self.query_one("#btn_args").disabled = not bool(entry.args)
        self.query_one("#btn_reset").disabled = False
        self._update_run_and_status(cmd_name)

    def _is_run_ready(self, cmd_name: str) -> bool:
        entry: CommandEntry | None = self.app.command_registry.get(cmd_name)  # type: ignore[attr-defined]
        if entry is None:
            return False
        if not entry.args:
            return True
        values = self._last_args_by_cmd.get(cmd_name)
        if values is None:
            return False  # Must open Args at least once, even if all args are optional
        return all(a.optional or a.name in values for a in entry.args)

    def _update_run_and_status(self, cmd_name: str) -> None:
        ready = self._is_run_ready(cmd_name)
        self.query_one("#btn_run").disabled = not ready
        lbl = self.query_one("#status_lbl", Label)
        if ready:
            lbl.update("Ready")
            lbl.remove_class("status-incomplete")
            lbl.add_class("status-ready")
        else:
            lbl.update("Incomplete")
            lbl.remove_class("status-ready")
            lbl.add_class("status-incomplete")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn_args":
            self._on_args()
        elif bid == "btn_reset":
            self._on_reset()
        elif bid == "btn_run":
            self._on_run()
        elif bid == "btn_next":
            self._on_next()
        elif bid == "btn_clear":
            self._on_clear()
        elif bid == "btn_copy":
            self._on_copy()
        elif bid == "btn_save_file":
            self._on_save()

    def _on_args(self) -> None:
        if not self._current_cmd:
            return
        entry: CommandEntry | None = self.app.command_registry.get(self._current_cmd)  # type: ignore[attr-defined]
        if entry is None:
            return
        current_values = self._last_args_by_cmd.get(self._current_cmd)

        def on_result(values: dict[str, Any] | None) -> None:
            if values is not None and self._current_cmd:
                self._last_args_by_cmd[self._current_cmd] = values
                self._update_run_and_status(self._current_cmd)

        self.app.push_screen(ArgsModal(entry, current_values), on_result)

    def _on_reset(self) -> None:
        if not self._current_cmd:
            return
        entry: CommandEntry | None = self.app.command_registry.get(self._current_cmd)  # type: ignore[attr-defined]
        if entry is None:
            return
        if not entry.args:
            self._last_args_by_cmd[self._current_cmd] = {}
        else:
            self._last_args_by_cmd.pop(self._current_cmd, None)
        self._update_run_and_status(self._current_cmd)

    def _on_run(self) -> None:
        if not self._current_cmd:
            return
        kwargs = dict(self._last_args_by_cmd.get(self._current_cmd) or {})
        self._cursor = None
        self._clear_result_status()
        self.run_worker(
            self._execute(self._current_cmd, kwargs, None),
            exclusive=True,
            group="execute",
        )

    def _on_next(self) -> None:
        if not self._current_cmd or self._cursor is None:
            return
        kwargs = dict(self._last_args_by_cmd.get(self._current_cmd) or {})
        self.run_worker(
            self._execute(self._current_cmd, kwargs, self._cursor),
            exclusive=True,
            group="execute",
        )

    def _on_clear(self) -> None:
        self._cursor = None
        self._clear_result_area()

    def _on_copy(self) -> None:
        if self._last_result_text:
            self.app.copy_to_clipboard(self._last_result_text)
            self._show_result_status("✓ Copied to clipboard")

    def _on_save(self) -> None:
        if not self._last_result_text:
            return

        def on_result(path: Path | None) -> None:
            if path is None:
                return
            try:
                path.write_text(self._last_result_text, encoding="utf-8")
                self._show_result_status(f"✓ Saved to {path.name}")
            except OSError as exc:
                self._show_result_status(f"✗ Save failed: {exc}", error=True)

        self.app.push_screen(SaveModal(), on_result)

    async def _execute(
        self, cmd_name: str, kwargs: dict[str, Any], cursor: bytes | None
    ) -> None:
        result: ReadResult = await self.app.service.execute_read(  # type: ignore[attr-defined]
            cmd_name, kwargs, cursor
        )
        if result.error:
            self._last_result_text = ""
            self._show_result_status(f"✗ {result.error}", error=True)
            self.query_one("#result_text", TextArea).load_text("")
            self.query_one("#export_row").display = False
            self.query_one("#btn_clear").display = False
            self.query_one("#btn_next").display = False
        else:
            self._cursor = result.cursor
            text = result.json_str or ""
            self._last_result_text = text
            self.query_one("#result_text", TextArea).load_text(text)
            entry: CommandEntry | None = self.app.command_registry.get(cmd_name)  # type: ignore[attr-defined]
            is_pageable = entry is not None and entry.pageable
            has_next = is_pageable and bool(result.cursor)
            self.query_one("#export_row").display = bool(text)
            self.query_one("#btn_clear").display = bool(text)
            self.query_one("#btn_next").display = has_next
            if has_next:
                self._show_result_status("✓ Success, use Next for more")
            else:
                self._show_result_status("✓ Success")

    def _show_result_status(self, message: str, error: bool = False) -> None:
        lbl = self.query_one("#result_status_lbl", Label)
        lbl.update(message)
        if error:
            lbl.remove_class("result-success")
            lbl.add_class("result-error")
        else:
            lbl.remove_class("result-error")
            lbl.add_class("result-success")
        lbl.display = True

    def _clear_result_status(self) -> None:
        self.query_one("#result_status_lbl", Label).display = False

    def _disable_actions(self) -> None:
        self.query_one("#btn_args").disabled = True
        self.query_one("#btn_reset").disabled = True
        self.query_one("#btn_run").disabled = True
        lbl = self.query_one("#status_lbl", Label)
        lbl.update("")
        lbl.remove_class("status-ready")
        lbl.remove_class("status-incomplete")

    async def _full_reset(self) -> None:
        self._current_cmd = None
        self._cursor = None
        self._last_args_by_cmd.clear()
        self.query_one("#cmd_select", Select).clear()
        self._clear_result_area()
        self._disable_actions()
