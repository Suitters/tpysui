#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Configuration screen for App."""

from functools import partial
import logging
from pathlib import Path
from typing import Any, Optional
from rich.text import Text
from textual import work, on, events
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.containers import Vertical, Container, Grid, HorizontalGroup
from textual.geometry import Offset
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

_ADD_NEW_TYPE: str = "ctrl+a"
_ADD_GRAPHQL_GROUP: str = "ctrl+l"
_ADD_GRPRC_GROUP: str = "ctrl+r"


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
        for row in cls._CONFIG_ROWS:
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
        row_values = [str(value) for value in data_table.get_row(row_key)]
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

    def show_popup(
        self, event: events.Click, in_table: Optional[EditableDataTable] = None
    ):
        raise NotImplementedError(f"show_popup event not handled.")

    def new_type_row(self, from_keys: str | None = None) -> None:
        """Faux abstraction for adding new row of Configuration type."""
        raise NotImplementedError(f"new_type_row not handled.")


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
        yield EditableDataTable(
            self, self._CG_EDITS, disable_delete=True, id="group_table"
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
        self.config_group_change(self.configuration.active_group)

    @work()
    async def standard_group(self, id: str):
        """."""
        if id == _ADD_GRPRC_GROUP:
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
                        Profile("testnet-archive", "archive.testnet.sui.io:443"),
                        Profile("mainnet-archive", "archive.mainnet.sui.io:443"),
                    ],
                ),
            )
        elif id == _ADD_GRAPHQL_GROUP:
            self.insert_standard_group(
                ProfileGroup(
                    PysuiConfiguration.SUI_GQL_RPC_GROUP,
                    "devnet",
                    "",
                    [],
                    [],
                    [],
                    [
                        Profile("devnet", "https://graphql.devnet.sui.io/graphql"),
                        Profile("testnet", "https://graphql.testnet.sui.io/graphql"),
                        Profile("mainnet", "https://graphql.mainnet.sui.io/graphql"),
                    ],
                )
            )

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
    async def add_group(self, event: ButtonStatic.Pressed | None = None):
        new_group: NewGroup = await self.app.push_screen_wait(
            AddGroup(self.configuration.group_names())
        )
        if new_group:
            prf_grp = ProfileGroup(new_group.name, "", "", [], [], [], [])
            self._insert_new_group(group=prf_grp, make_active=new_group.active)

    def new_type_row(self, from_keys: str | None = None):
        """Add new Group row of Configuration type."""
        if from_keys == _ADD_NEW_TYPE:
            logger.debug("Add new Group")
            self.add_group()
        elif from_keys == _ADD_GRPRC_GROUP:
            logger.debug("Add gRPC new Group")
            self.standard_group(_ADD_GRPRC_GROUP)
        elif from_keys == _ADD_GRAPHQL_GROUP:
            logger.debug("Add GraphQL new Group")
            self.standard_group(_ADD_GRAPHQL_GROUP)

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

    @work()
    async def popup_add_grpc_group(self, event: ButtonStatic.Pressed):
        logger.debug("Popup action...add gRPC group")
        self.standard_group(_ADD_GRPRC_GROUP)

    @work()
    async def popup_add_gql_group(self, event: ButtonStatic.Pressed):
        logger.debug("Popup action...add GraphQL group")
        self.standard_group(_ADD_GRAPHQL_GROUP)

    def show_popup(
        self, event: events.Click, in_table: EditableDataTable | None = None
    ):
        if not in_table:
            grpc_disabled = False
            gql_disabled = False
            if self.configuration:
                gnames: list[str] = self.configuration.group_names()
                grpc_disabled = PysuiConfiguration.SUI_GRPC_GROUP in gnames
                gql_disabled = PysuiConfiguration.SUI_GQL_RPC_GROUP in gnames
            else:
                grpc_disabled = gql_disabled = True
            action_list: list[MenuOption] = [
                MenuOption("Add Group...", self.configuration is None, self.add_group),
                MenuOption(
                    "Add gRPC Group...", grpc_disabled, self.popup_add_grpc_group
                ),
                MenuOption(
                    "Add GraphQL Group...", gql_disabled, self.popup_add_gql_group
                ),
            ]
            pu_ofs: Offset = Offset(
                x=self.offset.x + event.offset.x, y=self.content_region.y
            )
            self.app.push_screen(PopUpMenu(self, action_list, pu_ofs))
            logger.debug(f"Config Group Event in table {in_table}.")
        else:
            logger.debug(f"Forwarding to {in_table.id}")
            in_table.pop_up(event)


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
        CellConfig("URL", True, True),  # , [validator.URL()]
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
        yield EditableDataTable(
            self, self._CP_EDITS, disable_delete=True, id="profile_table"
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

    @work()
    async def add_profile(self, event: ButtonStatic.Pressed | None = None):
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

    def new_type_row(self, from_keys: str | None = None):
        """Add new Profile row of Configuration type."""
        if from_keys == _ADD_NEW_TYPE:
            logger.debug("Add new Profile")
            self.add_profile()

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

    def show_popup(
        self, event: events.Click, in_table: Optional[EditableDataTable] = None
    ):
        action_list: list[MenuOption] = [
            MenuOption("Add Profile...", self.configuration is None, self.add_profile)
        ]
        pu_ofs: Offset = Offset(
            x=self.offset.x + event.offset.x, y=self.content_region.y
        )
        self.app.push_screen(PopUpMenu(self, action_list, pu_ofs))

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
        yield EditableDataTable(
            self, self._CI_EDITS, disable_delete=True, id="identity_table"
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

    def new_type_row(self, from_keys: str | None = None):
        """Add new Identify row of Configuration type."""
        if from_keys == _ADD_NEW_TYPE:
            logger.debug("Add new Identity")
            self.add_identity()

    @work()
    async def add_identity(self, event: ButtonStatic.Pressed | None = None):
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

    def show_popup(
        self, event: events.Click, in_table: Optional[EditableDataTable] = None
    ):
        action_list: list[MenuOption] = [
            MenuOption("Add Identity...", self.configuration is None, self.add_identity)
        ]
        pu_ofs: Offset = Offset(
            x=self.offset.x + event.offset.x, y=self.content_region.y
        )
        self.app.push_screen(PopUpMenu(self, action_list, pu_ofs))
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
        self.new_configuration_work()

    @work()
    async def new_configuration_work(
        self, event: ButtonStatic.Pressed | None = None
    ) -> None:
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
        self.save_to_work()

    @work()
    async def save_to_work(self, event: ButtonStatic.Pressed | None = None) -> None:
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
        self.gen_to_work()

    @work()
    async def gen_to_work(self, event: ButtonStatic.Pressed | None = None) -> None:
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
        self.save_to_work()

    @work()
    async def save_to_work(self, event: ButtonStatic.Pressed | None = None) -> None:
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
        self.select_configuration_work()

    @work()
    async def select_configuration_work(
        self, event: ButtonStatic.Pressed | None = None
    ) -> None:
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

    @work()
    async def main_popup(self, event: events.Click) -> None:
        a_list: list[MenuOption] = [
            MenuOption(
                "Open Pysui Configuration...", False, self.select_configuration_work
            ),
            MenuOption(
                "New Pysui Configuration...", False, self.new_configuration_work
            ),
            MenuOption("Save As...", self.configuration is None, self.save_to_work),
            MenuOption(
                "Stub code from Configuration...",
                self.configuration is None,
                self.gen_to_work,
            ),
        ]
        self.app.push_screen(PopUpMenu(self, a_list, event.offset))

    def _determine_owner_from_key_event(self, event: events.Key) -> ConfigRow | None:
        """Determine focus (if any)"""
        parent = None
        if self.configuration and self.focused:
            if self.focused.id == "group_table":
                logger.debug(f"Group action to {self.focused.parent.id}")
                parent = self.focused.parent
            elif self.focused.id == "profile_table":
                logger.debug(f"Profile action to {self.focused.parent.id}")
                parent = self.focused.parent
            elif self.focused.id == "identity_table":
                logger.debug(f"Identity action to {self.focused.parent.id}")
                parent = self.focused.parent
        return parent

    def on_key(self, event: events.Key) -> None:
        """Handles key events.

        Args:
            event (events.Key): They keyboard event
        """
        if event.key == "ctrl+f":
            self.select_configuration_work()
        elif event.key == "ctrl+n":
            self.new_configuration_work()
        elif event.key == "ctrl+s":
            if self.configuration:
                self.save_to_work()
        elif event.key == "ctrl+g":
            if self.configuration:
                self.gen_to_work()
        elif event.key == _ADD_NEW_TYPE:
            logger.debug(f"{_ADD_NEW_TYPE} cfg:{self.configuration is not None}")
            parent = self._determine_owner_from_key_event(event)
            if parent:
                parent.new_type_row(event.key)
        elif event.key == _ADD_GRPRC_GROUP:
            logger.debug(f"ctrl+r (add gRPC) cfg:{self.configuration is not None}")
            parent = self._determine_owner_from_key_event(event)
            if (
                isinstance(parent, ConfigGroup)
                and PysuiConfiguration.SUI_GQL_RPC_GROUP
                not in parent.configuration.group_names()
            ):
                logger.debug(f"Add gRPC valid for {parent.id}")
                parent.new_type_row(event.key)
            else:
                logger.debug(f"No action on {parent.id}")
        elif event.key == _ADD_GRAPHQL_GROUP:
            logger.debug(f"ctrl+l (add gql) cfg:{self.configuration is not None}")
            parent = self._determine_owner_from_key_event(event)
            if (
                isinstance(parent, ConfigGroup)
                and PysuiConfiguration.SUI_GRPC_GROUP
                not in parent.configuration.group_names()
            ):
                logger.debug(f"Add GraphQL valid for {parent.id}")
                parent.new_type_row(event.key)
            else:
                logger.debug(f"No action on {parent.id}")

    def on_click(self, event: events.Click):
        """Handles mouse events, specifically watching for right mouse click.

        Args:
            event (events.Click): The mouse click event
        """
        if event.button == 3:

            wid: str = event.widget.id
            if wid and wid.endswith("table"):
                return
                owner: ConfigRow = event.widget.parent
                owner.show_popup(event, event.widget)
            logger.debug(f"Have mouse {wid}")
            event.stop()
            if wid:
                # Direct on edit table
                # if wid.endswith("table"):
                #     owner: ConfigRow = event.widget.parent
                #     owner.show_popup(event, event.widget)
                # Direct to profiles and identities
                if wid.endswith("row"):
                    event.widget.show_popup(event)
                # Indirect to group
                elif wid.endswith("horizontal"):
                    owner: ConfigRow = event.widget.parent
                    owner.show_popup(event)
            else:
                # This is in our space
                if event.widget.parent and event.widget.parent.id == "config-header":
                    logger.debug("Main popup")
                    self.main_popup(event)
                # No idea
                else:
                    owner = event.widget.parent if event.widget.parent else None
