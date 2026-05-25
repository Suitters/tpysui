#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from ..services.base import ActiveState


class _StateField(Static):
    """Clickable Static for the active-state row."""
    can_focus = False

    def __init__(self, text: str = "", on_click_cb=None, **kwargs) -> None:
        super().__init__(text, **kwargs)
        self._cb = on_click_cb

    def on_click(self) -> None:
        if self._cb:
            self._cb()


class ActiveStateBar(Widget):

    class ConfigChangeRequested(Message):
        pass

    class GroupChangeRequested(Message):
        pass

    state: reactive[ActiveState | None] = reactive(None)

    def compose(self) -> ComposeResult:
        with Horizontal(id="title-row"):
            yield Static("tpysui", id="title-text")
        with Horizontal(id="state-row"):
            yield _StateField(
                "", id="btn-config", classes="state-btn",
                on_click_cb=self._on_config_click,
            )
            yield Static("·", classes="sep")
            yield _StateField(
                "", id="btn-group", classes="state-btn",
                on_click_cb=self._on_group_click,
            )
            yield Static("·", classes="sep")
            yield Static("-", id="bar-profile", classes="state-label")
            yield Static("·", classes="sep")
            yield Static("-", id="bar-address", classes="state-label")

    def _on_config_click(self) -> None:
        self.post_message(self.ConfigChangeRequested())

    def _on_group_click(self) -> None:
        self.post_message(self.GroupChangeRequested())

    def set_area(self, label: str) -> None:
        self.query_one("#title-text", Static).update(f"tpysui ({label})")

    def set_state(self, state: ActiveState) -> None:
        self.state = state

    def watch_state(self, state: ActiveState | None) -> None:
        if state is None:
            return
        cfg_name = Path(state.config_path).name if state.config_path else "-"
        cfg_field = self.query_one("#btn-config", _StateField)
        cfg_field.update(cfg_name)
        cfg_field.tooltip = f"{state.config_path or '-'}\n(click to open a different config)"

        grp_field = self.query_one("#btn-group", _StateField)
        grp_field.update(state.group_name or "-")
        grp_field.tooltip = "Active group — click to switch"

        prof = self.query_one("#bar-profile", Static)
        prof.update(state.profile_name or "-")
        prof.tooltip = state.profile_url or "Active profile"

        addr = _short_addr(state.address)
        alias = state.address_alias or "-"
        addr_field = self.query_one("#bar-address", Static)
        addr_field.update(f"{alias} ({addr})")


def _short_addr(a: str | None) -> str:
    if not a:
        return "-"
    return f"{a[:6]}...{a[-4:]}" if len(a) > 12 else a
