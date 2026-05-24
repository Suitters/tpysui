from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class WritesScreen(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Data Writes -- arrives in Sprint 6")
