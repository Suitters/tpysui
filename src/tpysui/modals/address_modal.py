#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class AddressChoiceModal(ModalScreen[str | None]):
    """Returns 'generate' or 'import', or None if cancelled."""
    BINDINGS = [("escape", "cancel", "Cancel")]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Add Address", id="title")
            with Horizontal(id="buttons"):
                yield Button("Generate Keypair", variant="success", id="btn-generate")
                yield Button("Import Key",       variant="primary",  id="btn-import")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-generate":
            self.dismiss("generate")
        elif event.button.id == "btn-import":
            self.dismiss("import")

    def action_cancel(self) -> None:
        self.dismiss(None)


class AliasInputModal(ModalScreen[str | None]):
    """Single alias input — used for generate-keypair and rename-alias flows."""
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "OK"),
    ]

    def __init__(self, title: str, placeholder: str = "alias",
                 initial: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._placeholder = placeholder
        self._initial = initial

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self._title, id="modal-title")
            yield Label("Alias:")
            yield Input(value=self._initial, placeholder=self._placeholder, id="input-alias")
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="primary",  id="btn-cancel")
                yield Button("OK",     variant="success", id="btn-ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-ok":
            self.action_submit()
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        alias = self.query_one("#input-alias", Input).value.strip()
        if not alias:
            self.notify("Alias is required", severity="error")
            return
        self.dismiss(alias)


class ImportAddressModal(ModalScreen[dict | None]):
    """Returns {alias, private_key} or None if cancelled."""
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Import"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Import Address", id="modal-title")
            yield Label("Alias:")
            yield Input(placeholder="my-wallet", id="input-alias")
            yield Label("Private key (base64 or suiprivkey…):")
            yield Input(placeholder="suiprivkey...", id="input-key", password=True)
            with Horizontal(id="buttons"):
                yield Button("Cancel", variant="primary",  id="btn-cancel")
                yield Button("Import", variant="success", id="btn-import")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-import":
            self.action_submit()
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        alias = self.query_one("#input-alias", Input).value.strip()
        key   = self.query_one("#input-key",   Input).value.strip()
        if not alias or not key:
            self.notify("Alias and private key are required", severity="error")
            return
        self.dismiss({"alias": alias, "private_key": key})


class MnemonicModal(ModalScreen[None]):
    """Displays a mnemonic phrase once. User must click OK to dismiss."""
    BINDINGS = [("escape", "ok", "OK"), ("enter", "ok", "OK")]

    def __init__(self, alias: str, mnemonic: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._alias = alias
        self._mnemonic = mnemonic

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("New Keypair Created", id="modal-title")
            yield Static(
                "Record this mnemonic now — it will NOT be shown again.",
                id="warning",
            )
            yield Static(f"Alias: {self._alias}")
            yield Static(self._mnemonic, id="mnemonic")
            with Horizontal(id="buttons"):
                yield Button("OK — I have recorded it", variant="primary", id="btn-ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)

    def action_ok(self) -> None:
        self.dismiss(None)
