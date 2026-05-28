#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from textual.message import Message
from textual.widgets import Tree


class Sidebar(Tree[str]):
    AREAS = [
        ("Dashboard",                 "screen-dashboard"),
        ("Configuration & Key Mgmt", "screen-config"),
        ("Data Reads",               "screen-reads"),
        ("Utilities",                "screen-utilities"),
        ("Transaction Builder",      "screen-tx"),
        ("UCI Command Development",  "screen-uci"),
    ]
    _DESCRIPTIONS = {
        "screen-dashboard": "Active address overview: gas objects, owned objects, coin balances, chain info",
        "screen-config":    "Manage groups, profiles, and addresses in your PysuiConfig",
        "screen-reads":     "Query on-chain data: objects, balances, events, and more",
        "screen-utilities": "Submit transactions: transfers, coin management, and contract calls",
        "screen-tx":        "Build and inspect Programmable Transaction Blocks (PTBs)",
        "screen-uci":       "Develop and test UCI commands interactively",
    }

    class AreaSelected(Message):
        def __init__(self, screen_id: str) -> None:
            super().__init__()
            self.screen_id = screen_id

    def __init__(self, **kwargs) -> None:
        super().__init__("Areas", **kwargs)
        self.show_root = False
        self.guide_depth = 2
        self._suppress_msg = False

    def on_mount(self) -> None:
        for label, screen_id in self.AREAS:
            self.root.add_leaf(label, data=screen_id)
        self.root.expand()
        if self.root.children:
            self.select_node(self.root.children[0])

    def action_cursor_down(self) -> None:
        children = self.root.children
        if children and self.cursor_node is not None and self.cursor_node is children[-1]:
            self.select_node(children[0])
        else:
            super().action_cursor_down()

    def action_cursor_up(self) -> None:
        children = self.root.children
        if children and self.cursor_node is not None and self.cursor_node is children[0]:
            self.select_node(children[-1])
        else:
            super().action_cursor_up()

    def select_area(self, screen_id: str) -> None:
        for node in self.root.children:
            if node.data == screen_id:
                if self.cursor_node is node:
                    return
                self._suppress_msg = True
                self.select_node(node)
                break

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        event.stop()
        if event.node.data is not None:
            self.log(f"Sidebar -> {event.node.data}")
            self.tooltip = self._DESCRIPTIONS.get(event.node.data)
            if self._suppress_msg:
                self._suppress_msg = False
            else:
                self.post_message(self.AreaSelected(event.node.data))
