#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""UtilityConfirmModal — arg summary + Cancel / Simulate / Execute."""

from __future__ import annotations

from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from ..services.taxonomy_loader import CommandEntry

# Commands that cannot be simulated (they merge all coins; simulation is meaningless).
_NO_SIMULATE = frozenset({"smash-coins", "splay-coins"})


def _fmt_value(v: Any) -> str:
    if isinstance(v, list):
        return f"[{len(v)} {'entry' if len(v) == 1 else 'entries'}]"
    s = str(v)
    if len(s) > 48:
        return s[:22] + "…" + s[-10:]
    return s


class UtilityConfirmModal(ModalScreen[str | None]):
    """Show arg summary; dismiss with 'simulate', 'execute', or None (cancel)."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", priority=True)]

    def __init__(
        self,
        cmd_name: str,
        args: dict[str, Any],
        entry: CommandEntry | None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self._cmd_name = cmd_name
        self._args = args
        self._entry = entry

    @property
    def _simulate_disabled(self) -> bool:
        return self._cmd_name in _NO_SIMULATE

    def compose(self) -> ComposeResult:
        with Vertical(id="util_confirm_dialog"):
            yield Label(f"Run: {self._cmd_name}", id="util_confirm_title")
            yield Label("Arguments:", classes="util_confirm_section")
            with VerticalScroll(id="util_confirm_args_scroll"):
                if self._args:
                    for k, v in self._args.items():
                        yield Label(f"  {k}: {_fmt_value(v)}", classes="util_confirm_arg")
                else:
                    yield Label("  (no arguments)", classes="util_confirm_arg")
            if self._simulate_disabled:
                yield Label(
                    "Note: Simulate not available for this utility.",
                    classes="util_confirm_note",
                )
            with Horizontal(id="util_confirm_buttons"):
                yield Button("Cancel", id="btn_cancel", variant="default")
                yield Button(
                    "Simulate",
                    id="btn_simulate",
                    variant="warning",
                    disabled=self._simulate_disabled,
                )
                yield Button("Execute", id="btn_execute", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn_cancel":
            self.dismiss(None)
        elif bid == "btn_simulate":
            self.dismiss("simulate")
        elif bid == "btn_execute":
            self.dismiss("execute")

    def action_cancel(self) -> None:
        self.dismiss(None)
