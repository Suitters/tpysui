from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class ReadsScreen(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Data Reads -- arrives in Sprint 5")
