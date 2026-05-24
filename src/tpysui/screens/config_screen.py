import asyncio

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Static

from ..services.base import GroupInfo


class ConfigScreen(Widget):
    _groups: list[GroupInfo] = []

    DEFAULT_CSS = """
    ConfigScreen {
        layout: horizontal;
        width: 1fr;
        height: 1fr;
    }
    ConfigScreen .pane {
        height: 100%;
        border: solid $primary;
    }
    ConfigScreen #pane-groups {
        width: 1fr;
    }
    ConfigScreen #pane-profiles {
        width: 2fr;
    }
    ConfigScreen #pane-addresses {
        width: 2fr;
    }
    ConfigScreen .pane-title {
        dock: top;
        height: 1;
        background: $boost;
        padding: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(classes="pane", id="pane-groups"):
            yield Static("Groups", classes="pane-title")
            yield DataTable(id="groups-table", cursor_type="row")
        with Vertical(classes="pane", id="pane-profiles"):
            yield Static("Profiles", classes="pane-title", id="title-profiles")
            yield DataTable(id="profiles-table", cursor_type="row")
        with Vertical(classes="pane", id="pane-addresses"):
            yield Static("Addresses", classes="pane-title", id="title-addresses")
            yield DataTable(id="addresses-table", cursor_type="row")

    def on_mount(self) -> None:
        self.log("ConfigScreen mounted")
        self.query_one("#groups-table",    DataTable).add_columns("Active", "Name", "Protocol", "Profiles", "Addresses")
        self.query_one("#profiles-table",  DataTable).add_columns("Active", "Name", "URL")
        self.query_one("#addresses-table", DataTable).add_columns("Active", "Alias", "Address", "Scheme")

    def load(self) -> None:
        self._load_groups()

    @work(exclusive=True, group="config-groups", exit_on_error=False)
    async def _load_groups(self) -> None:
        self.log("Loading groups")
        groups = await self.app.service.list_groups()
        self._groups = groups
        gt = self.query_one("#groups-table", DataTable)
        gt.clear()
        for g in groups:
            marker = "*" if g.is_active else ""
            gt.add_row(marker, g.name, g.protocol.value, str(g.profile_count), str(g.address_count), key=g.name)
        if groups:
            gt.move_cursor(row=0)

    @work(exclusive=True, group="config-detail", exit_on_error=False)
    async def _load_for_group(self, group_name: str) -> None:
        self.log(f"Loading detail for {group_name}")
        profiles, addresses = await asyncio.gather(
            self.app.service.list_profiles(group_name),
            self.app.service.list_addresses(group_name),
        )
        self.query_one("#title-profiles", Static).update(f"Profiles ({group_name})")
        self.query_one("#title-addresses", Static).update(f"Addresses ({group_name})")
        group = next((g for g in self._groups if g.name == group_name), None)
        url_label = f"{group.protocol.value} URL" if group else "URL"
        pt = self.query_one("#profiles-table",  DataTable)
        at = self.query_one("#addresses-table", DataTable)
        pt.clear(columns=True)
        pt.add_columns("Active", "Name", url_label)
        for p in profiles:
            marker = "*" if p.is_active else ""
            pt.add_row(marker, p.name, p.url, key=p.name)
        if profiles:
            pt.move_cursor(row=0)
        at.clear()
        for a in addresses:
            short = f"{a.address[:8]}...{a.address[-6:]}"
            marker = "*" if a.is_active else ""
            at.add_row(marker, a.alias, short, a.key_scheme, key=a.address)
        if addresses:
            at.move_cursor(row=0)

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        if event.data_table.id == "groups-table" and event.row_key and event.row_key.value:
            self._load_for_group(event.row_key.value)
