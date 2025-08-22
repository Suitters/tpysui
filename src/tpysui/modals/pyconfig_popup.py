#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""PysuiConfiguration Window Popup Menu."""

from __future__ import annotations
from typing import Awaitable, Callable, Optional

from textual import events, on
from textual.app import ComposeResult
from textual.color import Color
from textual.containers import Container, Vertical
from textual.geometry import Offset
from textual.message import Message
from textual.screen import ModalScreen
from textual.visual import VisualType
from textual.widget import Widget
from textual.widgets import Static


class NoSelectStatic(Static):
    """This class is used in PopUpMenu to create buttons."""

    @property
    def allow_select(self) -> bool:
        return False


class ButtonStatic(NoSelectStatic):
    """This class is used in PopUpMenu to create buttons."""

    class Pressed(Message):
        def __init__(self, button: ButtonStatic) -> None:
            super().__init__()
            self.button = button

        @property
        def control(self) -> ButtonStatic:
            return self.button

    def __init__(
        self,
        content: VisualType = "",
        *,
        expand: bool = False,
        shrink: bool = False,
        markup: bool = True,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        position_index: int | None = None,
    ) -> None:
        super().__init__(
            content=content,
            expand=expand,
            shrink=shrink,
            markup=markup,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.position_index = position_index
        self.click_started_on: bool = False

    def on_mouse_down(self, event: events.MouseDown) -> None:

        self.add_class("pressed")
        self.click_started_on = True

    def on_mouse_up(self, event: events.MouseUp) -> None:

        self.remove_class("pressed")
        if self.click_started_on:
            self.post_message(self.Pressed(self))
            self.click_started_on = False

    def on_leave(self, event: events.Leave) -> None:

        self.remove_class("pressed")
        self.click_started_on = False


class PopUpMenu(ModalScreen[str | None]):

    DEFAULT_CSS = """
    PopUpMenu {
        background: $background 0%;       
        align: left top;    /* This will set the starting coordinates to (0, 0) */
    }                       /* Which we need for the absolute offset to work */
    #menu_container {
        background: $surface;        
        # width: 10; height: 3;                   
        border-left: wide $panel;
        border-right: wide $panel;                
        &.bottom { border-top: hkey $panel; }
        &.top { border-bottom: hkey $panel; }
        & > ButtonStatic {
            &:hover { background: $panel-lighten-2; }
            &.pressed { background: $primary; }        
        }
    }
    """

    def __init__(
        self,
        owner: Widget,
        action_list: list[str],
        menu_offset: Offset,
        callback_list: Optional[
            Callable[[ButtonStatic.Pressed], Awaitable[None]]
        ] = None,
    ):
        super().__init__()
        self.action_list = action_list
        self.owner = owner
        self.selected = None
        self.menu_offset = menu_offset
        if callback_list and len(callback_list) != len(action_list):
            raise ValueError("Callback list length must be equal to action_list")
        self.callback_list = callback_list

    def compose(self) -> ComposeResult:
        with Vertical(id="menu_container"):
            for index, action in enumerate(self.action_list):
                yield ButtonStatic(action, position_index=index)

    def on_mount(self) -> None:
        y_offset = self.menu_offset.y
        if y_offset == 0:
            y_offset += 1
        menu: Vertical = self.query_one("#menu_container", Vertical)
        menu.styles.width = len(max(self.action_list, key=len)) + 2
        menu.styles.height = len(self.action_list)
        menu.offset = Offset(self.menu_offset.x, y_offset)
        menu.styles.background = Color.parse("blue")

    @on(ButtonStatic.Pressed)
    async def button_pressed(self, event: ButtonStatic.Pressed) -> None:
        if event.button.position_index >= 0:
            if self.callback_list:
                fn = self.callback_list[event.button.position_index]
                fn(event)
            else:
                self.owner.post_message(event)
            self.dismiss(None)

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)
