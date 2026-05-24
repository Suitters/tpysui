from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from ..services.base import ActiveState


class ActiveStateBar(Widget):
    DEFAULT_CSS = """
    ActiveStateBar {
        height: 3;
    }
    ActiveStateBar Horizontal {
        height: 100%;
        align: left middle;
    }
    ActiveStateBar Static {
        padding: 0 1;
        width: auto;
    }
    ActiveStateBar .sep {
        color: $accent;
    }
    """

    state: reactive[ActiveState | None] = reactive(None)

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield Static("[Config] -",  id="bar-config")
            yield Static("|", classes="sep")
            yield Static("[Group] -",   id="bar-group")
            yield Static("|", classes="sep")
            yield Static("[Profile] -", id="bar-profile")
            yield Static("|", classes="sep")
            yield Static("[Address] -", id="bar-address")

    def set_state(self, state: ActiveState) -> None:
        self.state = state

    def watch_state(self, state: ActiveState | None) -> None:
        if state is None:
            return
        cfg_name = Path(state.config_path).name if state.config_path else "-"
        self.query_one("#bar-config",  Static).update(f"[Config] {cfg_name}")
        self.query_one("#bar-group",   Static).update(f"[Group] {state.group_name or '-'}")
        self.query_one("#bar-profile", Static).update(f"[Profile] {state.profile_name or '-'}")
        addr = _short_addr(state.address)
        alias = state.address_alias or "-"
        self.query_one("#bar-address", Static).update(f"[Address] {alias} ({addr})")


def _short_addr(a: str | None) -> str:
    if not a:
        return "-"
    return f"{a[:6]}...{a[-4:]}" if len(a) > 12 else a
