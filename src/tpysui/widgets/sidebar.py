from textual.message import Message
from textual.widgets import Tree


class Sidebar(Tree[str]):
    AREAS = [
        ("Configuration & Key Mgmt", "screen-config"),
        ("Data Reads",               "screen-reads"),
        ("Data Writes",              "screen-writes"),
        ("Transaction Builder",      "screen-tx"),
        ("UCI Command Development",  "screen-uci"),
    ]

    class AreaSelected(Message):
        def __init__(self, screen_id: str) -> None:
            super().__init__()
            self.screen_id = screen_id

    def __init__(self, **kwargs) -> None:
        super().__init__("Areas", **kwargs)
        self.show_root = False
        self.guide_depth = 2

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

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        event.stop()
        if event.node.data is not None:
            self.log(f"Sidebar -> {event.node.data}")
            self.post_message(self.AreaSelected(event.node.data))
