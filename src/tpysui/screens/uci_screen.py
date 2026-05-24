from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class UciScreen(Widget):
    def compose(self) -> ComposeResult:
        yield Static("UCI Command Development -- arrives in Sprint 8")
