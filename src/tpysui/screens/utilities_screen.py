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
from ..modals.utility_confirm_modal import UtilityConfirmModal
from ..services.base import ActiveState, UtilityResultDTO
from ..services.taxonomy_loader import CommandEntry


class UtilitiesScreen(Widget):
    """Area 4 — Blockchain Utilities."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._current_group: str | None = None
        self._current_cmd: str | None = None
        self._last_state: ActiveState | None = None
        self._last_args_by_cmd: dict[str, dict[str, Any] | None] = {}
        self._cmds_populated: bool = False
        self._last_result_text: str = ""

    def compose(self) -> ComposeResult:
        with Vertical(id="util_body"):
            with Horizontal(id="util_group_row"):
                yield Select(
                    [],
                    id="util_group_select",
                    allow_blank=True,
                    prompt="Select a group…",
                )
                yield Select(
                    [],
                    id="util_cmd_select",
                    allow_blank=True,
                    prompt="Select a utility…",
                )
            with Horizontal(id="util_action_row"):
                yield Button("Args...", id="util_btn_args", variant="primary", disabled=True)
                yield Label("", id="util_status_lbl")
                yield Button("Reset", id="util_btn_reset", variant="primary", disabled=True)
                yield Button("Run", id="util_btn_run", variant="primary", disabled=True)
            yield Label("", id="util_result_status_lbl")
            yield TextArea("", id="util_result_text", language="json", read_only=True)
            with Horizontal(id="util_export_row"):
                yield Button("Copy", id="util_btn_copy", variant="primary")
                yield Button("Save...", id="util_btn_save_file", variant="primary")

    def on_mount(self) -> None:
        self.query_one("#util_export_row").display = False
        self.query_one("#util_result_status_lbl").display = False

    async def on_show(self) -> None:
        if not self._cmds_populated:
            self._populate_groups()
            self._cmds_populated = True

        state = await self.app.service.active_state()  # type: ignore[attr-defined]
        if self._last_state is None:
            self._last_state = state

    def _populate_groups(self) -> None:
        _GROUP_ORDER = ["Coin Management", "Transfers", "Development"]
        available = {
            e.group
            for e in self.app.command_registry.values()  # type: ignore[attr-defined]
            if e.mode == "write"
        }
        groups = [g for g in _GROUP_ORDER if g in available]
        groups += sorted(available - set(_GROUP_ORDER))
        self.query_one("#util_group_select", Select).set_options([(g, g) for g in groups])

    def _get_commands_for_group(self, group: str) -> list[str]:
        return [
            name
            for name, entry in self.app.command_registry.items()  # type: ignore[attr-defined]
            if entry.mode == "write" and entry.group == group
        ]

    def notify_state_changed(self, new_state: ActiveState) -> None:
        if self._last_state is not None and (
            new_state.config_path != self._last_state.config_path
            or new_state.group_name != self._last_state.group_name
            or new_state.profile_name != self._last_state.profile_name
        ):
            self.run_worker(self._full_reset(), exclusive=True, group="reset")
        self._last_state = new_state

    @on(Select.Changed, "#util_group_select")
    def on_group_selected(self, event: Select.Changed) -> None:
        self._clear_result_area()
        cmd_select = self.query_one("#util_cmd_select", Select)
        if event.value is Select.BLANK:
            self._current_group = None
            self._current_cmd = None
            cmd_select.clear()
            self._disable_actions()
            return
        self._current_group = str(event.value)
        self._current_cmd = None
        cmds = self._get_commands_for_group(self._current_group)
        cmd_select.set_options([(c, c) for c in cmds])
        self._disable_actions()

    @on(Select.Changed, "#util_cmd_select")
    def on_command_selected(self, event: Select.Changed) -> None:
        self._clear_result_area()
        if event.value is Select.BLANK:
            self._current_cmd = None
            self._disable_actions()
            return
        cmd_name = str(event.value)
        self._current_cmd = cmd_name
        entry: CommandEntry | None = self.app.command_registry.get(cmd_name)  # type: ignore[attr-defined]
        if entry is None:
            return
        if entry.args or entry.custom_ui:
            self._last_args_by_cmd.pop(cmd_name, None)
        else:
            self._last_args_by_cmd.setdefault(cmd_name, {})
        self.query_one("#util_btn_args").disabled = not bool(entry.args) and not entry.custom_ui
        self.query_one("#util_btn_reset").disabled = False
        self._update_run_and_status(cmd_name)

    def _is_run_ready(self, cmd_name: str) -> bool:
        entry: CommandEntry | None = self.app.command_registry.get(cmd_name)  # type: ignore[attr-defined]
        if entry is None:
            return False
        if entry.custom_ui:
            values = self._last_args_by_cmd.get(cmd_name)
            if not values:
                return False
            if not values.get("directive_file"):
                return False
            targets = values.get("targets", [])
            if not targets:
                return False
            for t in targets:
                if not t.get("value") or not t.get("out_file"):
                    return False
                if t.get("type") == "GenericStructure":
                    if not any(k not in ("type", "value", "out_file") for k in t):
                        return False
            return True
        if not entry.args:
            return True
        values = self._last_args_by_cmd.get(cmd_name)
        if values is None:
            return False
        return all(a.optional or a.name in values for a in entry.args)

    def _update_run_and_status(self, cmd_name: str) -> None:
        ready = self._is_run_ready(cmd_name)
        self.query_one("#util_btn_run").disabled = not ready
        lbl = self.query_one("#util_status_lbl", Label)
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
        if bid == "util_btn_args":
            self._on_args()
        elif bid == "util_btn_reset":
            self._on_reset()
        elif bid == "util_btn_run":
            self._on_run()
        elif bid == "util_btn_copy":
            self._on_copy()
        elif bid == "util_btn_save_file":
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

        if entry.custom_ui:
            from ..modals.mtobcs_modal import MtobcsModal
            if current_values is not None:
                self.app.push_screen(MtobcsModal(current_values), on_result)
            else:
                from ..modals.mtobcs_launch_modal import MtobcsLaunchModal

                def on_launch(result: dict | None) -> None:
                    if result is None:
                        return
                    if result.get("action") == "load":
                        self.app.push_screen(MtobcsModal(result), on_result)
                    else:
                        self.app.push_screen(MtobcsModal(None), on_result)

                self.app.push_screen(MtobcsLaunchModal(), on_launch)
        else:
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
        cmd_name = self._current_cmd
        kwargs = dict(self._last_args_by_cmd.get(cmd_name) or {})
        entry: CommandEntry | None = self.app.command_registry.get(cmd_name)  # type: ignore[attr-defined]

        def on_confirm(action: str | None) -> None:
            if action is None:
                return
            self.run_worker(
                self._execute(cmd_name, kwargs, simulate=(action == "simulate")),
                exclusive=True,
                group="execute",
            )

        self.app.push_screen(UtilityConfirmModal(cmd_name, kwargs, entry), on_confirm)

    def _on_copy(self) -> None:
        if self._last_result_text:
            self.app.copy_to_clipboard(self._last_result_text)
            self.notify("Copied to clipboard")

    def _on_save(self) -> None:
        if not self._last_result_text:
            return

        def on_result(path: Path | None) -> None:
            if path is None:
                return
            try:
                path.write_text(self._last_result_text, encoding="utf-8")
                self.notify(f"Saved to {path.name}")
            except OSError as exc:
                self.notify(f"Save failed: {exc}", severity="error")

        self.app.push_screen(SaveModal(), on_result)

    async def _execute(self, cmd_name: str, kwargs: dict[str, Any], simulate: bool) -> None:
        result: UtilityResultDTO | None = None
        error_msg: str | None = None
        try:
            result = await self.app.service.run_utility(  # type: ignore[attr-defined]
                cmd_name, kwargs, simulate
            )
            if result.error:
                error_msg = result.error
        except Exception as exc:
            error_msg = str(exc) or f"{type(exc).__name__} (no message)"
        finally:
            self._refresh_dashboard()
        self._populate_result(result, error_msg)

    def _refresh_dashboard(self) -> None:
        from ..screens.dashboard_screen import DashboardScreen
        if self._last_state:
            self.app.query_one(DashboardScreen).notify_state_changed(self._last_state)

    def _populate_result(self, result: "UtilityResultDTO | None", error_msg: str | None) -> None:
        lbl = self.query_one("#util_result_status_lbl", Label)
        if error_msg:
            lbl.update(f"✗ {error_msg}")
            lbl.remove_class("status-result-ok")
            lbl.add_class("status-result-error")
            lbl.display = True
            self.query_one("#util_result_text", TextArea).load_text("")
            self._last_result_text = ""
            self.query_one("#util_export_row").display = False
        elif result:
            prefix = "Simulated" if result.simulated else "Executed"
            parts = [f"✓ {prefix}"]
            if result.digest:
                parts.append(f"digest: {result.digest}")
            if result.gas_used is not None:
                parts.append(f"gas: {result.gas_used:,} MIST")
            lbl.update("  |  ".join(parts))
            lbl.remove_class("status-result-error")
            lbl.add_class("status-result-ok")
            lbl.display = True
            json_text = result.raw_json or ""
            self.query_one("#util_result_text", TextArea).load_text(json_text)
            self._last_result_text = json_text
            self.query_one("#util_export_row").display = bool(json_text)
        else:
            lbl.display = False
            self.query_one("#util_result_text", TextArea).load_text("")
            self._last_result_text = ""
            self.query_one("#util_export_row").display = False

    def _clear_result_area(self) -> None:
        self._last_result_text = ""
        self._populate_result(None, None)

    def _disable_actions(self) -> None:
        self.query_one("#util_btn_args").disabled = True
        self.query_one("#util_btn_reset").disabled = True
        self.query_one("#util_btn_run").disabled = True
        lbl = self.query_one("#util_status_lbl", Label)
        lbl.update("")
        lbl.remove_class("status-ready")
        lbl.remove_class("status-incomplete")

    async def _full_reset(self) -> None:
        self._current_group = None
        self._current_cmd = None
        self._last_args_by_cmd.clear()
        self.query_one("#util_group_select", Select).clear()
        self.query_one("#util_cmd_select", Select).clear()
        self._clear_result_area()
        self._disable_actions()
