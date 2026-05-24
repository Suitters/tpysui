from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label


class ConfirmModal(ModalScreen[bool]):
    BINDINGS = [("escape", "cancel", "Cancel")]

    DEFAULT_CSS = """
    ConfirmModal {
        align: center middle;
    }
    ConfirmModal #dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    ConfirmModal #message {
        margin-bottom: 1;
    }
    ConfirmModal #buttons {
        align: right middle;
        height: auto;
    }
    ConfirmModal Button {
        margin-left: 1;
    }
    """

    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self._message, id="message")
            with Horizontal(id="buttons"):
                yield Button("Delete", variant="error",   id="btn-confirm")
                yield Button("Cancel", variant="primary", id="btn-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "btn-confirm")

    def action_cancel(self) -> None:
        self.dismiss(False)
