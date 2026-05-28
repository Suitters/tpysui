#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class UtilitiesScreen(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Utilities -- arrives in Sprint 6")
