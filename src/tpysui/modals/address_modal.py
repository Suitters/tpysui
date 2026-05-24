from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class AddressChoiceModal(ModalScreen[str | None]):
    """Returns 'generate' or 'import', or None if cancelled."""
    BINDINGS = [("escape", "cancel", "Cancel")]
    DEFAULT_CSS = """
    AddressChoiceModal { align: center middle; }
    AddressChoiceModal #dialog {
        width: 40; height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    AddressChoiceModal #title { text-style: bold; margin-bottom: 1; }
    AddressChoiceModal #buttons { align: center middle; height: auto; margin-top: 1; }
    AddressChoiceModal Button { margin: 0 1; }
    """

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
    DEFAULT_CSS = """
    AliasInputModal { align: center middle; }
    AliasInputModal #dialog {
        width: 50; height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    AliasInputModal #modal-title { text-style: bold; margin-bottom: 1; }
    AliasInputModal Label { color: $text-muted; }
    AliasInputModal #buttons { align: right middle; height: auto; margin-top: 1; }
    AliasInputModal Button { margin-left: 1; }
    """

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
                yield Button("OK",     variant="success", id="btn-ok")
                yield Button("Cancel", variant="primary",  id="btn-cancel")

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
    DEFAULT_CSS = """
    ImportAddressModal { align: center middle; }
    ImportAddressModal #dialog {
        width: 60; height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    ImportAddressModal #modal-title { text-style: bold; margin-bottom: 1; }
    ImportAddressModal Label { color: $text-muted; }
    ImportAddressModal Input { margin-bottom: 1; }
    ImportAddressModal #buttons { align: right middle; height: auto; margin-top: 1; }
    ImportAddressModal Button { margin-left: 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Import Address", id="modal-title")
            yield Label("Alias:")
            yield Input(placeholder="my-wallet", id="input-alias")
            yield Label("Private key (base64 or suiprivkey…):")
            yield Input(placeholder="suiprivkey...", id="input-key", password=True)
            with Horizontal(id="buttons"):
                yield Button("Import", variant="success", id="btn-import")
                yield Button("Cancel", variant="primary",  id="btn-cancel")

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
    DEFAULT_CSS = """
    MnemonicModal { align: center middle; }
    MnemonicModal #dialog {
        width: 64; height: auto;
        border: thick $warning;
        background: $surface;
        padding: 1 2;
    }
    MnemonicModal #modal-title { text-style: bold; margin-bottom: 1; }
    MnemonicModal #warning { color: $warning; margin-bottom: 1; }
    MnemonicModal #mnemonic { text-style: bold; margin-bottom: 1; }
    MnemonicModal #buttons { align: center middle; height: auto; margin-top: 1; }
    """

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
