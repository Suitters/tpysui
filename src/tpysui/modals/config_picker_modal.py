#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DirectoryTree, Static


class ConfigPickerModal(ModalScreen[str | None]):
    """Browse for a folder. When require_config=True the folder must contain PysuiConfig.json."""

    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(self, require_config: bool = True, **kwargs) -> None:
        super().__init__(**kwargs)
        self._require_config = require_config

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Open Config Folder", id="dialog-title")
            yield Static("[dim]Navigate to a folder containing PysuiConfig.json[/dim]", id="selected-path")
            yield DirectoryTree(Path.home(), id="picker-tree")
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="btn-cancel")

    def on_directory_tree_directory_selected(
        self, event: DirectoryTree.DirectorySelected
    ) -> None:
        path = event.path
        if not self._require_config:
            self.dismiss(str(path))
        elif (path / "PysuiConfig.json").exists():
            self.dismiss(str(path))
        else:
            self.query_one("#selected-path", Static).update(
                "[dim]No PysuiConfig.json in this folder[/dim]"
            )

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        path = event.path
        if not self._require_config:
            self.dismiss(str(path.parent))
        elif path.name == "PysuiConfig.json":
            self.dismiss(str(path.parent))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
