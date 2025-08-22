#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Configuration screen for App."""

from functools import partial
import logging
from pathlib import Path
from typing import Optional
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.containers import Vertical, Container, Grid, HorizontalGroup
from textual import on
from textual import events
from textual.reactive import reactive
from textual.screen import Screen
import textual.validation as validator
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Button,
)

from textual.widgets.data_table import RowKey, ColumnKey

from ..modals import *
from ..widgets import EditableDataTable, CellConfig, SimpleHeader

# from ..widgets.editable_table import EditableDataTable, CellConfig
# from ..widgets.simple_header import SimpleHeader
from ..utils import generate_python

from pysui import PysuiConfiguration
from pysui.sui.sui_common.config.confgroup import ProfileGroup, Profile


logger = logging.getLogger("config")


class ConfigRow(Container):
    """Base configuration container class."""

    _CONFIG_ROWS: list["ConfigRow"] = []
    configuration: reactive[PysuiConfiguration | None] = reactive(
        None, always_update=True
    )
    configuration_group: reactive[ProfileGroup | None] = reactive(
        None, always_update=True
    )

    def __init__(
        self, *children, name=None, id=None, classes=None, disabled=False, markup=True
    ):
        ConfigRow._CONFIG_ROWS.append(self)
        logger.debug(f"Instantiating {id}")
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )

    @classmethod
    def get_config(cls) -> None | PysuiConfiguration:
        """Gets the configuration in play else None."""
        for row in cls._CONFIG_ROWS:
            if not row.configuration:
                return None
            else:
                return row.configuration
        return None

    @classmethod
    def config_change(cls, config_path: Path) -> None:
        """Dispatch configuration change."""
        cpath: Path = (
            config_path.parent
            if config_path.name == "PysuiConfig.json"
            else config_path
        )
        pysuicfg = PysuiConfiguration(from_cfg_path=str(cpath))
        for index, row in enumerate(cls._CONFIG_ROWS):
            if index == 0:
                gnames: list[str] = pysuicfg.group_names()
                for idx, rb in enumerate(row.query("Button").nodes):
                    if idx == 0:
                        rb.disabled = False
                    elif idx == 1 and PysuiConfiguration.SUI_GRPC_GROUP not in gnames:
                        rb.disabled = False
                    elif (
                        idx == 2 and PysuiConfiguration.SUI_GQL_RPC_GROUP not in gnames
                    ):
                        rb.disabled = False
            else:
                row.query_one("Button").disabled = False
            row.configuration = pysuicfg

    @classmethod
    def config_group_change(cls, pgroup: ProfileGroup) -> None:
        """Dispatch a change in the active group."""
        for row in cls._CONFIG_ROWS:
            row.configuration_group = pgroup

    def _switch_active(
        self, cell: EditableDataTable.CellValueChange, c_key: ColumnKey
    ) -> Coordinate:
        """Change the active row."""
        new_active_coord: Coordinate = Coordinate(0, 0)
        # The current was 'Active', find an alternative or ignore if solo
        if cell.old_value == "Yes":
            new_active_coord = cell.table.switch_active_row(
                (1, "Yes"), (1, "No"), c_key, set_focus=True
            )
        elif cell.new_value == "Yes":
            # Update existing Yes to No and set current to Yes
            name = str(cell.table.get_cell_at(cell.coordinates.left()))
            new_active_coord = cell.table.switch_active_row(
                (1, "Yes"), (0, name), c_key, set_focus=True
            )
        return new_active_coord

    @on(EditableDataTable.RowDelete)
    def group_row_delete(self, selected: EditableDataTable.RowDelete):
        """Handle delete"""
        self.remove_row(selected.table, selected.row_key)

    @work
    async def remove_row(self, data_table: EditableDataTable, row_key: RowKey) -> None:
        row_values = [str(value) for value in data_table.get_row(row_key)[:-1]]
        confirmed = await self.app.push_screen_wait(
            ConfirmDeleteRowDialog(
                f"Are you sure you want to delete this row:\n[green]{row_values[0]}"
            )
        )
        if confirmed:
            self.dropping_row(data_table, row_key, row_values[0], row_values[1])

    def dropping_row(
        self,
        from_table: EditableDataTable,
        row_key: RowKey,
        row_name: str,
        active_flag: str,
    ) -> None:
        """Defult row removal."""
        raise NotImplementedError(
            f"Drop for '{row_name}' in {row_key} not implemented and active is {active_flag}."
        )

    def show_popup(self, in_table: Optional[EditableDataTable] = None):
        raise NotImplementedError(f"Event not handled.")


class ConfigGroup(ConfigRow):

    _CG_COLUMN_KEYS: list[ColumnKey] = None
    _CG_HEADER: tuple[str, str] = ("Name", "Active")
    _CG_EDITS: list[CellConfig] = [
        CellConfig("Name", True, True),
        CellConfig(
            "Active",
            True,
            False,
            None,
            partial(
                SingleChoiceDialog, "Switch State", "Change Group Active", ["Yes", "No"]
            ),
        ),
    ]

    def __init__(
        self, *children, name=None, id=None, classes=None, disabled=False, markup=True
    ):
        super().__init__(
            *children,
            name=name,
            id="group_row",
            classes=classes,
            disabled=disabled,
            markup=markup,
        )

    def compose(self):
        with HorizontalGroup(id="group_horizontal"):
            yield Button(
                "Add",
                compact=True,
                variant="primary",
                id="add_group",
                disabled=True,
            )
            yield Button(
                "Add gRPC Group",
                compact=True,
                variant="primary",
                id="add_grpc_group",
                disabled=True,
            )
            yield Button(
                "Add GraphQL Group",
                compact=True,
                variant="primary",
                id="add_graphql_group",
                disabled=True,
            )
        yield EditableDataTable(
            self, self._CG_EDITS, disable_delete=False, id="group_table"
        )

    def validate_group_name(self, table: EditableDataTable, in_value: str) -> bool:
        """Validate no rename collision."""
        coordinate = table.cursor_coordinate
        pre_value = str(table.get_cell_at(coordinate))
        if pre_value == in_value:
            pass
        elif in_value in self.configuration.group_names():
            return False
        return True

    def on_mount(self) -> None:
        self.border_title = self.name
        table: EditableDataTable = self.query_one("#group_table")
        self._CG_COLUMN_KEYS = table.add_columns(*self._CG_HEADER)
        self._CG_EDITS[0].validators = [
            validator.Length(minimum=3, maximum=32),
            validator.Function(
                partial(self.validate_group_name, table), "Group name not unique."
            ),
        ]
        table.focus()

    def _update_button_state(self):
        gnames: list[str] = self.configuration.group_names()
        grpc_b = self.query_one("#add_grpc_group", Button)
        if PysuiConfiguration.SUI_GRPC_GROUP in gnames:
            grpc_b.disabled = True
        else:
            grpc_b.disabled = False
        graphql_b = self.query_one("#add_graphql_group", Button)
        if PysuiConfiguration.SUI_GQL_RPC_GROUP in gnames:
            graphql_b.disabled = True
        else:
            graphql_b.disabled = False

    def _insert_new_group(self, group: ProfileGroup, make_active: bool):
        """Insert a group into the current configuraiton and update UI.

        Args:
            group (ProfileGroup): The PysuiConfiguration group being added
            make_active (bool): If this group should become the active group
        """
        table: EditableDataTable = self.query_one("#group_table")
        self.configuration.model.add_group(group=group, make_active=make_active)
        number = table.row_count + 1
        label = Text(str(number), style="#B0FC38 italic")

        table.add_row(
            *[Text(group.group_name), Text("No")],
            label=label,
        )
        if make_active:
            self.configuration.model.group_active = group.group_name
            table.switch_active_row(
                (1, "Yes"),
                (0, group.group_name),
                self._CG_COLUMN_KEYS[1],
                set_focus=True,
            )
        self.configuration.save()
        self._update_button_state()
        self.config_group_change(self.configuration.active_group)

    @on(Button.Pressed)
    async def handle_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for creating new groups.

        Adding gRPC or GraphQL default groups only enabled if the
        standard names don't already exist in the configuration.

        Args:
            event (Button.Pressed): The button pressed message
        """
        if event.button.id == "add_grpc_group":
            self.insert_standard_group(
                ProfileGroup(
                    PysuiConfiguration.SUI_GRPC_GROUP,
                    "devnet",
                    "",
                    [],
                    [],
                    [],
                    [
                        Profile("devnet", "fullnode.devnet.sui.io:443"),
                        Profile("testnet", "fullnode.testnet.sui.io:443"),
                        Profile("mainnet", "fullnode.mainnet.sui.io:443"),
                    ],
                ),
            )
        elif event.button.id == "add_graphql_group":
            self.insert_standard_group(
                ProfileGroup(
                    PysuiConfiguration.SUI_GQL_RPC_GROUP,
                    "devnet",
                    "",
                    [],
                    [],
                    [],
                    [
                        Profile("devnet", "https://sui-devnet.mystenlabs.com/graphql"),
                        Profile(
                            "testnet", "https://sui-testnet.mystenlabs.com/graphql"
                        ),
                        Profile(
                            "mainnet", "https://sui-mainnetnet.mystenlabs.com/graphql"
                        ),
                    ],
                )
            )
        elif event.button.id == "add_group":
            self.add_group()

    @work()
    async def insert_standard_group(self, target_pgroup: ProfileGroup):
        from_group: list[str] = []
        for gname in self.configuration.group_names():
            agrp = self.configuration.model.get_group(group_name=gname)
            if agrp.key_list:
                from_group.append(gname)

        if from_group:
            igrp: InjectConfig
            if igrp := await self.app.push_screen_wait(
                InjectGroup(target_pgroup.group_name, from_group)
            ):
                if igrp.keys_from:
                    kgroup: ProfileGroup = self.configuration.model.get_group(
                        group_name=igrp.keys_from
                    )
                    target_pgroup.alias_list = kgroup.alias_list
                    target_pgroup.key_list = kgroup.key_list
                    target_pgroup.address_list = kgroup.address_list
                    target_pgroup.using_address = kgroup.using_address

                self._insert_new_group(group=target_pgroup, make_active=True)

    @work()
    async def add_group(self):
        new_group: NewGroup = await self.app.push_screen_wait(
            AddGroup(self.configuration.group_names())
        )
        if new_group:
            prf_grp = ProfileGroup(new_group.name, "", "", [], [], [], [])
            self._insert_new_group(group=prf_grp, make_active=new_group.active)

    def dropping_row(
        self,
        from_table: EditableDataTable,
        row_key: RowKey,
        row_name: str,
        active_flag: str,
    ) -> None:
        # Change PysuiConfig
        if from_table.row_count > 1:
            new_active = self.configuration.model.remove_group(group_name=row_name)
            # Handle active switch
            grp_change = None
            if active_flag == "Yes" and new_active:
                from_table.switch_active_row(
                    (0, row_name), (0, new_active), self._CG_COLUMN_KEYS[1]
                )
                grp_change: ProfileGroup = self.configuration.active_group
            # Delete from table
            from_table.remove_row(row_key)
            # Update add buttons
            self._update_button_state()
            # Save PysuiConfig
            self.configuration.save()
            if grp_change:
                self.config_group_change(grp_change)
        else:
            self.app.push_screen(OkPopup("[red]Can not delete only group"))

    @on(EditableDataTable.CellValueChange)
    def cell_change(self, cell: EditableDataTable.CellValueChange):
        """When a cell changes"""
        if cell.old_value != cell.new_value:
            # Group has been renamed
            if cell.cell_config.field_name == "Name":
                group = self.configuration.model.get_group(group_name=cell.old_value)
                group.group_name = cell.new_value
                if self.configuration.model.group_active == cell.old_value:
                    self.configuration.model.group_active = cell.new_value
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
            # Active status changed
            elif cell.cell_config.field_name == "Active":
                new_coord = self._switch_active(cell, self._CG_COLUMN_KEYS[1])
                gname = str(cell.table.get_cell_at(new_coord))
                self.configuration.model.group_active = gname
                group = self.configuration.model.get_group(group_name=gname)
            self._update_button_state()
            self.configuration.save()
            self.config_group_change(group)

    def watch_configuration(self, cfg: PysuiConfiguration):
        """Called when a new configuration is selected."""
        if cfg:
            table: EditableDataTable = self.query_one("#group_table")
            # Empty table
            table.clear()
            # Iterate group names and capture the active group
            active_row = 0
            for number, group in enumerate(cfg.group_names(), start=1):
                label = Text(str(number), style="#B0FC38 italic")
                if group == cfg.active_group_name:
                    active = "Yes"
                    active_row = number - 1
                else:
                    active = "No"
                table.add_row(*[Text(group), Text(active)], label=label)
            # Select the active row/column
            table.move_cursor(row=active_row, column=0, scroll=True)
            # Notify group listeners
            self.config_group_change(cfg.active_group)

    @on(DataTable.CellSelected)
    def group_cell_select(self, selected: DataTable.CellSelected):
        """Handle selection."""
        # A different group is selected.
        if selected.coordinate.column == 0 and selected.coordinate.row >= 0:
            gval = str(selected.value)
            self.config_group_change(
                self.configuration.model.get_group(group_name=gval)
            )

    def show_popup(self, in_table: Optional[EditableDataTable] = None):
        logger.debug(f"Config Group Event in table {in_table}.")


class ConfigProfile(ConfigRow):

    _CP_COLUMN_KEYS: list[ColumnKey] = None
    _CP_HEADER: tuple[str, str] = ("Name", "Active", "URL")
    _CP_EDITS: list[CellConfig] = [
        CellConfig("Name", True, True),
        CellConfig(
            "Active",
            True,
            False,
            None,
            partial(SingleChoiceDialog, "Switch State", "Change Active", ["Yes", "No"]),
        ),
        CellConfig("URL", True, True, [validator.URL()]),
    ]

    def __init__(
        self, *children, name=None, id=None, classes=None, disabled=False, markup=True
    ):
        super().__init__(
            *children,
            name=name,
            id="profile_row",
            classes=classes,
            disabled=disabled,
            markup=markup,
        )

    def compose(self):
        yield Button(
            "Add", variant="primary", compact=True, id="add_profile", disabled=True
        )
        yield EditableDataTable(
            self, self._CP_EDITS, disable_delete=False, id="profile_table"
        )

    def on_mount(self) -> None:
        self.border_title = self.name
        table: EditableDataTable = self.query_one("#profile_table")
        self._CP_COLUMN_KEYS = table.add_columns(*self._CP_HEADER)
        self._CP_EDITS[0].validators = [
            validator.Length(minimum=3, maximum=32),
            validator.Function(
                partial(self.validate_profile_name, table), "Profile name not unique."
            ),
        ]

    @on(Button.Pressed, "#add_profile")
    async def on_add_profile(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        self.add_profile()

    @work()
    async def add_profile(self):
        new_profile: NewProfile = await self.app.push_screen_wait(
            AddProfile(self.configuration_group.profile_names)
        )
        if new_profile:
            table: EditableDataTable = self.query_one("#profile_table")
            prf = Profile(new_profile.name, new_profile.url)
            self.configuration_group.add_profile(
                new_prf=prf, make_active=new_profile.active
            )
            number = table.row_count + 1
            label = Text(str(number), style="#B0FC38 italic")
            table.add_row(
                *[Text(new_profile.name), Text("No"), Text(new_profile.url)],
                label=label,
            )
            if new_profile.active:
                table.switch_active_row(
                    (1, "Yes"),
                    (0, new_profile.name),
                    self._CP_COLUMN_KEYS[1],
                    set_focus=True,
                )
            self.configuration.save()

    def dropping_row(
        self,
        from_table: EditableDataTable,
        row_key: RowKey,
        row_name: str,
        active_flag: str,
    ) -> None:
        # Change PysuiConfig
        new_active = self.configuration_group.remove_profile(profile_name=row_name)
        # Handle active switch
        if active_flag == "Yes" and new_active:
            from_table.switch_active_row(
                (0, row_name), (0, new_active), self._CP_COLUMN_KEYS[1]
            )
        # Delete from table
        from_table.remove_row(row_key)
        # Save PysuiConfig
        self.configuration.save()

    def validate_profile_name(self, table: EditableDataTable, in_value: str) -> bool:
        """Validate no rename collision."""
        coordinate = table.cursor_coordinate
        pre_value = str(table.get_cell_at(coordinate))
        if pre_value == in_value:
            pass
        elif in_value in self.configuration_group.profile_names:
            return False
        return True

    @on(EditableDataTable.CellValueChange)
    def cell_change(self, cell: EditableDataTable.CellValueChange):
        """When a cell changes"""
        if cell.old_value != cell.new_value:
            if cell.cell_config.field_name == "Name":
                profile = self.configuration_group.get_profile(
                    profile_name=cell.old_value
                )
                profile.profile_name = cell.new_value
                if self.configuration_group.using_profile == cell.old_value:
                    self.configuration_group.using_profile = cell.new_value
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
            elif cell.cell_config.field_name == "Active":
                active_coord = self._switch_active(cell, self._CP_COLUMN_KEYS[1])
                self.configuration_group.using_profile = str(
                    cell.table.get_cell_at(active_coord)
                )
            elif cell.cell_config.field_name == "URL":
                profile_name = cell.table.get_cell_at(cell.coordinates.left().left())
                profile = self.configuration_group.get_profile(
                    profile_name=str(profile_name)
                )
                profile.url = cell.new_value
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
            self.configuration.save()

    def watch_configuration_group(self, cfg: ProfileGroup):
        table: EditableDataTable = self.query_one("#profile_table")
        # Empty table
        table.clear()
        self.border_title = self.name
        if cfg:
            # Label it
            self.border_title = self.name + f" in {cfg.group_name}"
            # Setup row label
            counter = 1
            # Build content
            active_row = 0
            for profile in cfg.profiles:
                label = Text(str(counter), style="#B0FC38 italic")
                if profile.profile_name == cfg.using_profile:
                    active = "Yes"
                    active_row = counter - 1
                else:
                    active = "No"
                table.add_row(
                    *[Text(profile.profile_name), Text(active), Text(profile.url)],
                    label=label,
                )
                counter += 1
            # Select the active row/column
            table.move_cursor(row=active_row, column=0, scroll=True)

    def show_popup(self, in_table: Optional[EditableDataTable] = None):
        logger.debug(f"Config Profile Event in table {in_table}.")


class ConfigIdentities(ConfigRow):

    _CI_COLUMN_KEYS: list[ColumnKey] = None
    _CI_HEADER: tuple[str, str, str] = ("Alias", "Active", "Public Key", "Address")
    _CI_EDITS: list[CellConfig] = [
        CellConfig("Alias", True, True),
        CellConfig(
            "Active",
            True,
            False,
            None,
            partial(SingleChoiceDialog, "Switch State", "Change Active", ["Yes", "No"]),
        ),
        CellConfig("Public Key", False),
        CellConfig("Address", False),
    ]

    def __init__(
        self, *children, name=None, id=None, classes=None, disabled=False, markup=True
    ):
        super().__init__(
            *children,
            name=name,
            id="identities_row",
            classes=classes,
            disabled=disabled,
            markup=markup,
        )

    def compose(self):
        yield Button(
            "Add", variant="primary", compact=True, disabled=True, id="add_identity"
        )
        yield EditableDataTable(
            self, self._CI_EDITS, disable_delete=False, id="identity_table"
        )

    def on_mount(self) -> None:
        self.border_title = self.name
        table: EditableDataTable = self.query_one("#identity_table")
        self._CI_EDITS[0].validators = [
            validator.Length(minimum=3, maximum=64),
            validator.Function(
                partial(self.validate_alias_name, table), "Alias name not unique."
            ),
        ]
        self._CI_COLUMN_KEYS = table.add_columns(*self._CI_HEADER)

    @on(Button.Pressed, "#add_identity")
    async def on_add_profile(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        self.add_identity()

    @work()
    async def add_identity(self):
        alias_list = [x.alias for x in self.configuration_group.alias_list]
        new_ident: NewIdentity | None = await self.app.push_screen_wait(
            AddIdentity(alias_list)
        )

        if new_ident:
            # Generate the new key based on user input
            mnem, addy, prfkey, prfalias = self.configuration_group.new_keypair_parts(
                of_keytype=new_ident.key_scheme,
                word_counts=new_ident.word_count,
                derivation_path=new_ident.derivation_path,
                alias=new_ident.alias,
                alias_list=alias_list,
            )
            # Update the table
            table: EditableDataTable = self.query_one("#identity_table")
            number = table.row_count + 1
            label = Text(str(number), style="#B0FC38 italic")
            table.add_row(
                *[
                    Text(new_ident.alias),
                    Text("No"),
                    Text(prfalias.public_key_base64),
                    Text(addy),
                ],
                label=label,
            )
            # Settle active
            if new_ident.active:
                table.switch_active_row(
                    (1, "Yes"),
                    (0, new_ident.alias),
                    self._CI_COLUMN_KEYS[1],
                    set_focus=True,
                )
            # Add to group
            self.configuration_group.add_keypair_and_parts(
                new_address=addy,
                new_alias=prfalias,
                new_key=prfkey,
                make_active=new_ident.active,
            )
            _ = await self.app.push_screen_wait(NewKey(mnem, prfkey.private_key_base64))
            self.configuration.save()

    def dropping_row(
        self,
        from_table: EditableDataTable,
        row_key: RowKey,
        row_name: str,
        active_flag: str,
    ) -> None:
        # Change PysuiConfig
        new_active = self.configuration_group.remove_alias(alias_name=row_name)
        # Handle active switch
        if active_flag == "Yes" and new_active:
            from_table.switch_active_row(
                (0, row_name), (0, new_active), self._CI_COLUMN_KEYS[1]
            )
        # Delete from table
        from_table.remove_row(row_key)
        # Save PysuiConfig
        self.configuration.save()

    def validate_alias_name(self, table: EditableDataTable, in_value: str) -> bool:
        """Validate no rename collision."""
        coordinate = table.cursor_coordinate
        pre_value = str(table.get_cell_at(coordinate))
        if pre_value == in_value:
            pass
        elif in_value in [x.alias for x in self.configuration_group.alias_list]:
            return False
        return True

    @on(EditableDataTable.CellValueChange)
    def cell_change(self, cell: EditableDataTable.CellValueChange):
        """When a cell edit occurs"""
        if cell.old_value != cell.new_value:
            if cell.cell_config.field_name == "Alias":
                for pfa in self.configuration_group.alias_list:
                    if pfa.alias == cell.old_value:
                        pfa.alias = cell.new_value
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
            elif cell.cell_config.field_name == "Active":
                new_coord = (
                    self._switch_active(cell, self._CI_COLUMN_KEYS[1])
                    .right()
                    .right()
                    .right()
                )
                addy = str(cell.table.get_cell_at(new_coord))
                self.configuration_group.using_address = addy
            self.configuration.save()

    def watch_configuration_group(self, cfg: ProfileGroup):
        table: EditableDataTable = self.query_one("#identity_table")  # type: ignore
        # Empty table
        table.clear()
        self.border_title = self.name
        if cfg:
            self.border_title = self.name + f" in {cfg.group_name}"
            # Setup row label
            counter = 1
            # Build content
            active_row = 0
            indexer = len(cfg.address_list)
            for i in range(indexer):
                label = Text(str(i + 1), style="#B0FC38 italic")
                alias = cfg.alias_list[i]
                addy = cfg.address_list[i]
                if addy == cfg.using_address:
                    active = "Yes"
                    active_row = i
                else:
                    active = "No"
                table.add_row(
                    *[
                        Text(alias.alias),
                        Text(active),
                        Text(alias.public_key_base64),
                        Text(addy),
                    ],
                    label=label,
                )
            # Select the active row/column
            table.move_cursor(row=active_row, column=0, scroll=True)

    def show_popup(self, in_table: Optional[EditableDataTable] = None):
        logger.debug(f"Config Identities Event in table {in_table}.")


class PyCfgScreen(Screen[None]):
    """."""

    DEFAULT_CSS = """
    $background: black;
    $surface: black;

    #config-header {
        background:green;
    }
    #app-grid {
        layout: grid;
        grid-size: 1;
        grid-columns: 1fr;
        grid-rows: 1fr;
    }    
    #top-right {
        height: 100%;
        background: $panel;
    }    
    Button {
        margin-right: 1;
    }
    ConfigRow {
        padding: 1 1;
        border-title-color: green;
        border-title-style: bold;        
        width: 100%;
        border: white;
        background: $background;
        height:2fr;
        margin-right: 1;        
    }
    EditableDataTable {
        border: gray;
        background:$background;
    }
    #config-list {
        border:green;
        background:$background;
    }
    """

    BINDINGS = [
        ("ctrl+f", "select", "Select config"),
        ("ctrl+s", "savecfg", "Save a copy"),
        ("ctrl+g", "genstub", "Generate a Pyton stub"),
        ("ctrl+n", "newcfg", "Create a new config"),
    ]

    configuration: reactive[PysuiConfiguration | None] = reactive(None, bindings=True)

    def __init__(
        self,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ):
        self.config_sections = [
            ("Groups", ConfigGroup),
            ("Profiles", ConfigProfile),
            ("Identities", ConfigIdentities),
        ]
        super().__init__(name, "pysui_cfg", classes)

    def compose(self) -> ComposeResult:
        yield SimpleHeader(id="config-header")
        # yield Header(id="config-header")
        self.title = "Pysui Configuration: (ctrl+f to select)"
        with Grid(id="app-grid"):
            # yield ConfigSelection(id="config-list")
            with Vertical(id="top-right"):
                for section_name, section_class in self.config_sections:
                    yield section_class(name=section_name)
        yield Footer()

    async def action_newcfg(self) -> None:
        """Create a new PysuiConfig.yaml."""
        self.new_configuration()

    @work()
    async def new_configuration(self) -> None:
        """Do the work for creatinig new configuration."""

        def check_selection(selected: NewConfig | None) -> None:
            """Called when ConfigSaver is dismissed."""
            if selected:
                gen_maps: list[dict] = []
                if selected.setup_graphql:
                    gen_maps.append(
                        {
                            "name": PysuiConfiguration.SUI_GQL_RPC_GROUP,
                            "graphql_from_sui": True,
                            "grpc_from_sui": False,
                        }
                    )
                if selected.setup_grpc:
                    gen_maps.append(
                        {
                            "name": PysuiConfiguration.SUI_GRPC_GROUP,
                            "graphql_from_sui": False,
                            "grpc_from_sui": True,
                        }
                    )
                gen_maps.append(
                    {
                        "name": PysuiConfiguration.SUI_USER_GROUP,
                        "graphql_from_sui": False,
                        "grpc_from_sui": False,
                        "make_active": True,
                    }
                )
                self.configuration = PysuiConfiguration.initialize_config(
                    in_folder=selected.config_path, init_groups=gen_maps
                )
                ConfigRow.config_change(selected.config_path)

        self.app.push_screen(NewConfiguration(), check_selection)

    async def action_savecfg(self) -> None:
        """Save configuration to new location."""
        self.save_to()

    @work()
    async def save_to(self) -> None:
        """Run save to modal dialog."""

        def check_selection(selected: Path | None) -> None:
            """Called when ConfigSaver is dismissed."""
            if selected:
                new_fq_path = selected / "PysuiConfig.json"
                if crc := ConfigRow.get_config():
                    crc.save_to(selected)
                # Notify change
                self.title = f"Pysui Configuration: {new_fq_path}"
                ConfigRow.config_change(new_fq_path)
                # Update footer
                self.configuration = ConfigRow.get_config()

        self.app.push_screen(ConfigSaver(), check_selection)

    async def action_genstub(self) -> None:
        """Generate a Python stub"""
        self.gen_to()

    @work()
    async def gen_to(self) -> None:
        """Fetch a location."""

        def check_selection(selected: GenSpec | None) -> None:
            """Called when ConfigSaver is dismissed."""
            if selected:
                generate_python(
                    gen_spec=selected,
                    from_config=ConfigRow.get_config(),
                )

        self.app.push_screen(ConfigGener(), check_selection)

    async def action_savecfg(self) -> None:
        """Save configuration to new location."""
        self.save_to()

    @work()
    async def save_to(self) -> None:
        """Run save to modal dialog."""

        def check_selection(selected: Path | None) -> None:
            """Called when ConfigSaver is dismissed."""
            if selected:
                new_fq_path = selected / "PysuiConfig.json"
                if crc := ConfigRow.get_config():
                    crc.save_to(selected)
                # Notify change
                self.title = f"Pysui Configuration: {new_fq_path}"
                ConfigRow.config_change(new_fq_path)
                # Update footer
                self.configuration = ConfigRow.get_config()

        self.app.push_screen(ConfigSaver(), check_selection)

    async def action_select(self) -> None:
        self.select_configuration()

    @work()
    async def select_configuration(self) -> None:
        """Run selection modal dialog."""

        def check_selection(selected: Path | None) -> None:
            """Called when ConfigPicker is dismissed."""
            if selected:
                self.title = f"Pysui Configuration: {selected}"
                ConfigRow.config_change(selected)
                self.configuration = ConfigRow.get_config()

        self.app.push_screen(
            ConfigPicker(config_accept="PysuiConfig.json"), check_selection
        )

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Check if an action may run."""
        if action in ["savecfg", "genstub", "edit"] and self.configuration is None:
            return None
        return True

    @on(ButtonStatic.Pressed)
    async def button_pressed(self, event: ButtonStatic.Pressed) -> None:
        logger.debug(f"Received {event.button.id}")

    @work()
    async def main_popup(self, event: events.Click) -> None:
        event.offset
        self.app.push_screen(PopUpMenu(self, ["Fin", "Foo", "Bar"], event.offset))

    def on_click(self, event: events.Click):
        if event.button == 3:
            event.stop()
            wid: str = event.widget.id
            logger.debug(f"Right mouse for {wid}. Event stopped.")
            if wid:
                # Direct on edit table
                if wid.endswith("table"):
                    owner: ConfigRow = event.widget.parent
                    logger.debug(f"Table {wid} of {owner.id} with {self.configuration}")
                    owner.show_popup(event.widget)
                # Direct to profiles and identities
                elif wid.endswith("row"):
                    logger.debug(f"Widget id: {wid} context with {self.configuration}")
                    event.widget.show_popup()
                # Indirect to group
                elif wid.endswith("horizontal"):
                    owner: ConfigRow = event.widget.parent
                    logger.debug(
                        f"HorzBar id: {wid} of {owner.id} context with {self.configuration}"
                    )
                    owner.show_popup()
            else:
                # This is in our space
                if event.widget.parent and event.widget.parent.id == "config-header":
                    logger.debug(
                        f"Header id: {event.widget.parent.id} context with {self.configuration}"
                    )
                    self.main_popup(event)
                # No idea
                else:
                    owner = event.widget.parent if event.widget.parent else None
                    logger.debug(
                        f"No id:{type(event.widget)} on {owner} with {self.configuration}"
                    )
