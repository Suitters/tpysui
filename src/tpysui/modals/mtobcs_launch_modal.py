#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""MtobcsLaunchModal — entry chooser for move-struct-to-bcs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label

from ..modals.save_modal import SaveModal


class MtobcsLaunchModal(ModalScreen[dict | None]):
    """Choose Load Existing or Create New for move-struct-to-bcs."""

    BINDINGS = [Binding("escape", "cancel", "Cancel", priority=True)]

    def compose(self) -> ComposeResult:
        with Vertical(id="mtobcs_launch_dialog"):
            yield Label(
                "Load an existing Move to BCS Json Configuration file"
                " or continue on to create a new one.",
                id="mtobcs_launch_text",
            )
            with Horizontal(id="mtobcs_launch_buttons"):
                yield Button("Cancel", id="btn_launch_cancel", variant="default")
                yield Button("Load Existing…", id="btn_launch_load", variant="primary")
                yield Button("Create New...", id="btn_launch_new", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn_launch_cancel":
            self.dismiss(None)
        elif bid == "btn_launch_load":
            self._load_existing()
        elif bid == "btn_launch_new":
            self.dismiss({"action": "new"})

    def _load_existing(self) -> None:
        def on_result(path: Path | None) -> None:
            if path is None:
                return
            p = Path(str(path))
            if not p.exists():
                return
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                self.dismiss({
                    "action": "load",
                    "directive_file": str(p),
                    "targets": data.get("targets", []),
                    "_dirty": False,
                })
            except (json.JSONDecodeError, OSError):
                pass
        self.app.push_screen(SaveModal(mode="load"), on_result)

    def action_cancel(self) -> None:
        self.dismiss(None)
