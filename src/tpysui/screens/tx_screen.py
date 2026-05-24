from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class TxScreen(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Transaction Builder -- arrives in Sprint 7")
