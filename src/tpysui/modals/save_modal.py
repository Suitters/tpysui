#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Input, Label


class SaveModal(ModalScreen[Path | None]):
    """Directory browser + filename input for saving result JSON."""

    BINDINGS = [("escape", "action_cancel", "Cancel")]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._selected_dir: Path = Path.home()

    def compose(self) -> ComposeResult:
        with Vertical(id="save_dialog"):
            yield Label("Save Result", id="save_title")
            yield DirectoryTree(str(Path.home()), id="dir_tree")
            with Horizontal(id="save_filename_row"):
                yield Label("Filename:")
                yield Input(value="result.json", id="filename_inp")
            with Horizontal(id="save_buttons"):
                yield Button("Cancel", id="btn_cancel", variant="default")
                yield Button("Save", id="btn_save", variant="primary")

    @on(DirectoryTree.DirectorySelected)
    def on_dir_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        self._selected_dir = event.path

    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        self._selected_dir = event.path.parent
        self.query_one("#filename_inp", Input).value = event.path.name

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn_save":
            filename = self.query_one("#filename_inp", Input).value.strip()
            if filename:
                self.dismiss(self._selected_dir / filename)
        elif event.button.id == "btn_cancel":
            self.action_cancel()

    def action_cancel(self) -> None:
        self.dismiss(None)
