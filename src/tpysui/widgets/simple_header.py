#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Simplified Header that does not expand."""

from textual import events
from textual.widgets import Header


class SimpleHeader(Header):

    def __init__(
        self,
        show_clock=False,
        *,
        name=None,
        id=None,
        classes=None,
        icon=None,
        time_format=None,
    ):
        super().__init__(
            show_clock,
            name=name,
            id=id,
            classes=classes,
            icon=icon,
            time_format=time_format,
        )

    # def _on_click(self):
    #     pass

    def on_click(self, event: events.MouseEvent):
        event.prevent_default()
