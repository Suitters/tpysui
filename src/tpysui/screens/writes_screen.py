#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import Static


class WritesScreen(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Data Writes -- arrives in Sprint 6")
