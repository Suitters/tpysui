import asyncio

from textual import work
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widget import Widget
from textual.widgets import DataTable, Static

from ..services.base import ActiveStateChanged, GroupInfo
from ..modals.group_modal import GroupModal
from ..modals.profile_modal import ProfileModal
from ..modals.address_modal import (
    AddressChoiceModal, AliasInputModal, ImportAddressModal, MnemonicModal,
)
from ..modals.confirm_modal import ConfirmModal


class ConfigScreen(Widget):
    BINDINGS = [
        ("n", "new_row",    "New"),
        ("d", "delete_row", "Delete"),
        ("e", "edit_row",   "Edit"),
        ("a", "set_active", "Set Active"),
    ]
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
    ConfigScreen #pane-groups    { width: 1fr; }
    ConfigScreen #pane-profiles  { width: 2fr; }
    ConfigScreen #pane-addresses { width: 2fr; }
    ConfigScreen .pane-title {
        dock: top;
        height: 1;
        background: $boost;
        padding: 0 1;
    }
    ConfigScreen DataTable {
        scrollbar-size-horizontal: 0;
    }
    """

    def on_mount(self) -> None:
        self.log("ConfigScreen mounted")
        self._groups: list[GroupInfo] = []
        self._current_group: str = ""
        self.query_one("#groups-table",    DataTable).add_columns(
            "Active", "Name", "Protocol", "Profiles", "Addresses"
        )
        self.query_one("#profiles-table",  DataTable).add_columns("Active", "Name", "URL")
        self.query_one("#addresses-table", DataTable).add_columns("Active", "Alias", "Address", "Scheme")

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

    def load(self) -> None:
        self._load_groups()

    # --- helpers ---

    def _focused_pane(self) -> str:
        focused = self.app.focused
        if focused and focused.id == "profiles-table":
            return "profiles"
        if focused and focused.id == "addresses-table":
            return "addresses"
        return "groups"

    def _cursor_key(self, table_id: str) -> str | None:
        t = self.query_one(f"#{table_id}", DataTable)
        if t.row_count == 0:
            return None
        try:
            cell_key = t.coordinate_to_cell_key(t.cursor_coordinate)
            return cell_key.row_key.value
        except Exception:
            return None

    def _cursor_row_values(self, table_id: str) -> list | None:
        t = self.query_one(f"#{table_id}", DataTable)
        if t.row_count == 0:
            return None
        try:
            return list(t.get_row_at(t.cursor_row))
        except Exception:
            return None

    # --- loaders ---

    @work(exclusive=True, group="config-groups", exit_on_error=False)
    async def _load_groups(self) -> None:
        self.log("Loading groups")
        groups = await self.app.service.list_groups()
        self._groups = groups
        gt = self.query_one("#groups-table", DataTable)
        gt.clear()
        active_row = 0
        for i, g in enumerate(groups):
            marker = "*" if g.is_active else ""
            gt.add_row(marker, g.name, g.protocol.value,
                       str(g.profile_count), str(g.address_count), key=g.name)
            if g.is_active:
                active_row = i
        if groups:
            gt.move_cursor(row=active_row)

    @work(exclusive=True, group="config-groups", exit_on_error=False)
    async def _reload_groups_select(self, select_name: str) -> None:
        groups = await self.app.service.list_groups()
        self._groups = groups
        gt = self.query_one("#groups-table", DataTable)
        gt.clear()
        for g in groups:
            marker = "*" if g.is_active else ""
            gt.add_row(marker, g.name, g.protocol.value,
                       str(g.profile_count), str(g.address_count), key=g.name)
        target_row = 0
        for i, g in enumerate(groups):
            if g.name == select_name:
                target_row = i
                break
        if groups:
            gt.move_cursor(row=target_row)

    @work(exclusive=True, group="config-detail", exit_on_error=False)
    async def _load_for_group(self, group_name: str) -> None:
        self.log(f"Loading detail for {group_name}")
        self._current_group = group_name
        profiles, addresses = await asyncio.gather(
            self.app.service.list_profiles(group_name),
            self.app.service.list_addresses(group_name),
        )
        self.query_one("#title-profiles",  Static).update(f"Profiles ({group_name})")
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

    # --- actions ---

    def action_new_row(self) -> None:
        pane = self._focused_pane()
        if pane == "groups":
            self._new_group()
        elif pane == "profiles":
            self._new_profile()
        else:
            self._new_address()

    def action_delete_row(self) -> None:
        pane = self._focused_pane()
        if pane == "groups":
            self._delete_group()
        elif pane == "profiles":
            self._delete_profile()
        else:
            self._delete_address()

    def action_edit_row(self) -> None:
        pane = self._focused_pane()
        if pane == "profiles":
            self._edit_profile()
        elif pane == "addresses":
            self._rename_alias()

    def action_set_active(self) -> None:
        pane = self._focused_pane()
        if pane == "groups":
            key = self._cursor_key("groups-table")
            if key:
                self._do_set_active_group(key)
        elif pane == "profiles":
            key = self._cursor_key("profiles-table")
            if key and self._current_group:
                self._do_set_active_profile(self._current_group, key)
        else:
            row = self._cursor_row_values("addresses-table")
            if row and self._current_group:
                alias = row[1]
                self._do_set_active_address(self._current_group, alias)

    # --- new flows ---

    def _new_group(self) -> None:
        def on_result(data: dict | None) -> None:
            if data:
                self._do_create_group(data)
        self.app.push_screen(GroupModal(), on_result)

    def _new_profile(self) -> None:
        if not self._current_group:
            return
        def on_result(data: dict | None) -> None:
            if data:
                self._do_create_profile(data["name"], data["url"])
        self.app.push_screen(ProfileModal(), on_result)

    def _new_address(self) -> None:
        if not self._current_group:
            return
        def on_choice(choice: str | None) -> None:
            if choice == "generate":
                def on_alias(alias: str | None) -> None:
                    if alias:
                        self._do_generate_keypair(alias)
                self.app.push_screen(AliasInputModal("Generate Keypair"), on_alias)
            elif choice == "import":
                def on_import(data: dict | None) -> None:
                    if data:
                        self._do_import_address(data["alias"], data["private_key"])
                self.app.push_screen(ImportAddressModal(), on_import)
        self.app.push_screen(AddressChoiceModal(), on_choice)

    # --- delete flows ---

    def _delete_group(self) -> None:
        gt = self.query_one("#groups-table", DataTable)
        if gt.row_count <= 1:
            self.notify("Cannot delete the only group", severity="error")
            return
        key = self._cursor_key("groups-table")
        if not key:
            return
        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._do_delete_group(key)
        self.app.push_screen(
            ConfirmModal(f"Delete group [bold]{key}[/bold]?"), on_confirm
        )

    def _delete_profile(self) -> None:
        if not self._current_group:
            return
        key = self._cursor_key("profiles-table")
        if not key:
            return
        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._do_delete_profile(self._current_group, key)
        self.app.push_screen(
            ConfirmModal(f"Delete profile [bold]{key}[/bold]?"), on_confirm
        )

    def _delete_address(self) -> None:
        if not self._current_group:
            return
        row = self._cursor_row_values("addresses-table")
        if not row:
            return
        alias = row[1]
        def on_confirm(confirmed: bool) -> None:
            if confirmed:
                self._do_delete_address(self._current_group, alias)
        self.app.push_screen(
            ConfirmModal(f"Delete address [bold]{alias}[/bold]?"), on_confirm
        )

    # --- edit flows ---

    def _edit_profile(self) -> None:
        if not self._current_group:
            return
        key = self._cursor_key("profiles-table")
        row = self._cursor_row_values("profiles-table")
        if not key or not row:
            return
        current_url = row[2]
        def on_result(data: dict | None) -> None:
            if data:
                self._do_update_profile(key, data["url"])
        self.app.push_screen(
            ProfileModal(title="Edit Profile", name=key, url=current_url), on_result
        )

    def _rename_alias(self) -> None:
        if not self._current_group:
            return
        row = self._cursor_row_values("addresses-table")
        if not row:
            return
        current_alias = row[1]
        def on_result(new_alias: str | None) -> None:
            if new_alias and new_alias != current_alias:
                self._do_rename_alias(current_alias, new_alias)
        self.app.push_screen(
            AliasInputModal("Rename Alias", placeholder="new-alias", initial=current_alias),
            on_result,
        )

    # --- mutation workers ---

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_create_group(self, data: dict) -> None:
        await self.app.service.create_group(
            data["name"], data["protocol"], data["profiles"], data["keys"]
        )
        self._reload_groups_select(data["name"])

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_delete_group(self, name: str) -> None:
        new_active = await self.app.service.delete_group(name)
        self._reload_groups_select(new_active)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_set_active_group(self, name: str) -> None:
        state = await self.app.service.set_active_group(name)
        self.post_message(ActiveStateChanged(state))
        self._reload_groups_select(name)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_create_profile(self, name: str, url: str) -> None:
        await self.app.service.create_profile(self._current_group, name, url)
        self._load_for_group(self._current_group)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_update_profile(self, name: str, url: str) -> None:
        await self.app.service.update_profile(self._current_group, name, url)
        self._load_for_group(self._current_group)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_delete_profile(self, group_name: str, name: str) -> None:
        await self.app.service.delete_profile(group_name, name)
        self._load_for_group(group_name)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_set_active_profile(self, group_name: str, name: str) -> None:
        state = await self.app.service.set_active_profile(group_name, name)
        self.post_message(ActiveStateChanged(state))
        self._load_for_group(group_name)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_generate_keypair(self, alias: str) -> None:
        addr_info, mnemonic = await self.app.service.generate_keypair(
            self._current_group, alias
        )
        self.app.push_screen(MnemonicModal(alias, mnemonic))
        self._reload_groups_select(self._current_group)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_import_address(self, alias: str, private_key: str) -> None:
        await self.app.service.import_address(self._current_group, alias, private_key)
        self._reload_groups_select(self._current_group)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_rename_alias(self, existing: str, new_alias: str) -> None:
        await self.app.service.rename_alias(self._current_group, existing, new_alias)
        self._load_for_group(self._current_group)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_delete_address(self, group_name: str, alias: str) -> None:
        await self.app.service.delete_address(group_name, alias)
        self._reload_groups_select(group_name)

    @work(exclusive=True, group="config-mutate", exit_on_error=False)
    async def _do_set_active_address(self, group_name: str, alias: str) -> None:
        state = await self.app.service.set_active_address(group_name, alias)
        self.post_message(ActiveStateChanged(state))
        self._load_for_group(group_name)
