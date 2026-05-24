from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static


class ProfileModal(ModalScreen[dict | None]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Save"),
    ]

    def __init__(self, title: str = "Add Profile",
                 name: str = "", url: str = "", **kwargs) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._init_name = name
        self._init_url = url

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static(self._title, id="modal-title")
            yield Label("Name:")
            yield Input(value=self._init_name, placeholder="profile-name", id="input-name")
            yield Label("URL:")
            yield Input(value=self._init_url, placeholder="https://...", id="input-url")
            with Horizontal(id="buttons"):
                yield Button("Save",   variant="success", id="btn-save")
                yield Button("Cancel", variant="primary",  id="btn-cancel")

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
        if not name or not url:
            self.notify("Name and URL are required", severity="error")
            return
        self.dismiss({"name": name, "url": url})
