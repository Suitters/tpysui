#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static

from ..constants import NETWORK_TYPES
from ..utils.validators import suggest_network_type


class ProfileModal(ModalScreen[dict | None]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Save"),
    ]

    def __init__(self, title: str = "Add Profile",
                 name: str = "", url: str = "", network_type: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._init_name = name
        self._init_url = url
        self._init_network_type = network_type
        self._network_type_touched = False
        self._updating_select = False

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self._title, id="modal-title")
            yield Label("Name:")
            yield Input(value=self._init_name, placeholder="profile-name", id="input-name")
            yield Label("URL:")
            yield Input(value=self._init_url, placeholder="https://...", id="input-url")
            yield Label("Network Type:")
            yield Select([(v, v) for v in NETWORK_TYPES], value=self._init_network_type or suggest_network_type(self._init_url), id="input-network-type", allow_blank=False)
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="primary",  id="btn-cancel")
                yield Button("Save",   variant="success", id="btn-save")

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "input-url" and not self._network_type_touched:
            new_url = event.value
            suggested = suggest_network_type(new_url)
            select = self.query_one("#input-network-type", Select)
            self._updating_select = True
            select.value = suggested
            self._updating_select = False

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.control.id == "input-network-type" and not self._updating_select:
            self._network_type_touched = True

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-save":
            self.action_submit()
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        name = self.query_one("#input-name", Input).value.strip()
        url  = self.query_one("#input-url",  Input).value.strip()
        network_type = self.query_one("#input-network-type", Select).value
        if not name or not url:
            self.notify("Name and URL are required", severity="error")
            return
        if not network_type:
            self.notify("Network Type is required", severity="error")
            return
        self.dismiss({"name": name, "url": url, "network_type": network_type})
