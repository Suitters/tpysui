#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, ListView, ListItem


class ChooserModal(ModalScreen[str | None]):
    """Generic single-choice list modal. Returns the selected value or None."""
    BINDINGS = [("escape", "cancel", "Cancel")]

    def __init__(
        self,
        title: str,
        choices: list[str],
        labels: list[str] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._title = title
        self._choices = choices
        self._labels = labels if labels is not None else choices

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self._title, id="title")
            yield ListView(
                *[
                    ListItem(Label(label), name=value)
                    for label, value in zip(self._labels, self._choices)
                ],
                id="choice-list",
            )
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="btn-cancel")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self.dismiss(event.item.name)

    def on_button_pressed(self, _: Button.Pressed) -> None:
        self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)
