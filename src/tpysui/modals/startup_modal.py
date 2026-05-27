#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Static

from ..constants import SUI_GQL_GROUP, SUI_GRPC_GROUP
from ..services.base import GroupProtocol
from .config_picker_modal import ConfigPickerModal


class StartupModal(ModalScreen[dict | None]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Welcome to tpysui", id="dialog-title")
            with Horizontal(id="choice-buttons"):
                yield Button("New Config", variant="success", id="btn-new")
                yield Button("Open Existing", variant="primary", id="btn-open")
            with Vertical(id="new-section"):
                yield Label("Config folder:", classes="field-label")
                with Horizontal(id="new-folder-row"):
                    yield Input(placeholder="~/path/to/config/folder", id="new-folder")
                    yield Button("Browse…", id="btn-browse-new")
                yield Label("Initial groups:", classes="field-label")
                yield Checkbox("GraphQL group", value=True, id="chk-gql")
                yield Checkbox("gRPC group", value=False, id="chk-grpc")
                with Horizontal(id="action-buttons"):
                    yield Button("Create", variant="success", id="btn-create")
                    yield Button("Back", id="btn-back-new")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-new":
            self.query_one("#choice-buttons").display = False
            self.query_one("#new-section").display = True
        elif bid == "btn-open":
            self.app.push_screen(ConfigPickerModal(), self._on_config_picked)
        elif bid == "btn-back-new":
            self.query_one("#choice-buttons").display = True
            self.query_one("#new-section").display = False
        elif bid == "btn-browse-new":
            self.app.push_screen(ConfigPickerModal(require_config=False), self._on_folder_browsed)
        elif bid == "btn-create":
            self._submit_new()

    def _on_config_picked(self, path: str | None) -> None:
        if path:
            self.dismiss({"action": "open", "path": path})

    def _on_folder_browsed(self, path: str | None) -> None:
        if path:
            self.query_one("#new-folder", Input).value = path

    def _submit_new(self) -> None:
        folder = self.query_one("#new-folder", Input).value.strip()
        if not folder:
            self.notify("Folder path is required", severity="error")
            return
        gql = self.query_one("#chk-gql", Checkbox).value
        grpc = self.query_one("#chk-grpc", Checkbox).value
        if not gql and not grpc:
            self.notify("Select at least one group type", severity="error")
            return
        init_groups: list[dict] = []
        first = True
        if gql:
            init_groups.append(
                {"name": SUI_GQL_GROUP, "protocol": GroupProtocol.GRAPHQL, "make_active": first}
            )
            first = False
        if grpc:
            init_groups.append(
                {"name": SUI_GRPC_GROUP, "protocol": GroupProtocol.GRPC, "make_active": first}
            )
        self.dismiss({"action": "new", "folder": folder, "init_groups": init_groups})

    def action_cancel(self) -> None:
        self.dismiss(None)
