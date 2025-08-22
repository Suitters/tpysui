#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Mysten Sui Configuration screen for App."""

import base64
from copy import deepcopy
import dataclasses
from functools import partial
import hashlib
import json
from pathlib import Path
from typing import Optional
import dataclasses_json
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.containers import Vertical, Container, Grid
from textual import on
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen
import textual.validation as validator
from textual.widgets import (
    Footer,
    Header,
    Button,
)

from textual.widgets.data_table import RowKey, ColumnKey
import yaml

from ..modals import *

from ..widgets.editable_table import EditableDataTable, CellConfig
from pysui import PysuiConfiguration
from pysui.sui.sui_crypto import keypair_from_keystring
from pysui.sui.sui_common.config.confmodel import PysuiConfigModel
from pysui.sui.sui_common.config.confgroup import (
    ProfileGroup,
    Profile,
    ProfileKey,
    ProfileAlias,
)
import pysui.sui.sui_common.config.conflegacy as legacy


class ConfigRow(Container):
    """Base configuration grid container class."""

    _CONFIG_ROWS: list["ConfigRow"] = []

    CLIENT_YAML: Path = None
    CLIENT_ALIAS: Path = None
    CLIENT_KEYS: Path = None

    configuration: reactive[legacy.ConfigSui | None] = reactive(
        None, always_update=True
    )

    class GroupActiveChange(Message):
        """Raised when the active state of environment changes."""

        def __init__(
            self,
            target: str,
            new_value: str,
        ):
            self.new_value: str = new_value
            self.target = target
            super().__init__()

    class EnvironmentChange(Message):
        """Raised when the active state of environment changes.

        This applies to Name and URL.
        """

        def __init__(
            self,
            action: str,
            env_context: str,
            target: str,
            old_value: str,
            new_value: str,
        ):
            self.action: str = action
            self.env_context: str = env_context
            self.old_value: str = old_value
            self.new_value: str = new_value
            self.target = target
            super().__init__()

    class EnvironmentAdd(Message):
        """Raised when a new environment is defined."""

        def __init__(
            self,
            profile: NewProfile,
        ):
            self.profile = profile
            super().__init__()

    class EnvironmentDelete(Message):
        """Raised when a new environment is defined."""

        def __init__(self, env_context: str, new_active: str):
            self.env_context: str = env_context
            self.new_active: str = new_active
            super().__init__()

    def __init__(
        self, *children, name=None, id=None, classes=None, disabled=False, markup=True
    ):
        ConfigRow._CONFIG_ROWS.append(self)
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )

    @classmethod
    def load_sui_config(cls, client_path: Path) -> None:
        """Load the sui configuration from client.yaml"""
        cls.CLIENT_YAML = client_path
        cls.CLIENT_ALIAS = client_path.parent / "sui.aliases"
        # load client.yaml
        cfg_sui = legacy.ConfigSui.from_dict(
            yaml.safe_load(cls.CLIENT_YAML.read_text(encoding="utf8"))
        )
        # Check sui.keystore
        cls.CLIENT_KEYS = Path(cfg_sui.keystore.File)
        if not cls.CLIENT_KEYS.exists():
            raise ValueError(f"Keystore file {cls.CLIENT_KEYS} does not exist")
        for srow in cls._CONFIG_ROWS:
            if not isinstance(srow, ConfigGroup):
                srow.query_one("Button").disabled = False
            srow.configuration = cfg_sui

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

    @on(GroupActiveChange)
    def handle_active_value_change(self, msg: GroupActiveChange):
        """Handle a change of active environment or address value."""
        # Get the configuration main, update appropriate values
        # and save
        cfg: legacy.ConfigSui = self._CONFIG_ROWS[0].configuration
        if msg.target == "address":
            cfg.active_address = msg.new_value
        else:
            cfg.active_env = msg.new_value
        self.CLIENT_YAML.write_text(yaml.safe_dump(cfg.to_dict()))
        # Update the visuals
        self._CONFIG_ROWS[0].handle_active_value_change(msg)

    @on(EnvironmentChange)
    def handle_env_value_change(self, msg: EnvironmentChange):
        """Handle edits to environment rows."""
        cfg: legacy.ConfigSui = self._CONFIG_ROWS[0].configuration
        env_target: legacy.ConfigEnv = None
        for tenv in cfg.envs:
            if tenv.alias == msg.env_context:
                env_target = tenv
                break
        if not env_target:
            raise ValueError(f"{msg.env_context} not found in environment profiles.")
        if msg.action == "rename":
            if msg.target == "Name":
                if cfg.active_env == msg.old_value:
                    cfg.active_env = msg.new_value
                    self._CONFIG_ROWS[0].handle_active_value_change(
                        self.GroupActiveChange("name", msg.new_value)
                    )
                env_target.alias = msg.new_value
            elif msg.target == "URL":
                env_target.rpc = msg.new_value
            else:
                raise ValueError(f"No known property {msg.target}")
        else:
            raise ValueError(f"Action {msg.action} not supported.")
        self.CLIENT_YAML.write_text(yaml.safe_dump(cfg.to_dict()))

    @on(EnvironmentAdd)
    def handle_env_add(self, msg: EnvironmentAdd):
        """Handle additions to the environment (Profile) table."""
        cfg: legacy.ConfigSui = self._CONFIG_ROWS[0].configuration
        env: legacy.ConfigEnv = legacy.ConfigEnv(msg.profile.name, msg.profile.url)
        cfg.envs.append(env)
        if msg.profile.active:
            cfg.active_env = msg.profile.name
            self._CONFIG_ROWS[0].handle_active_value_change(
                self.GroupActiveChange("name", msg.profile.name)
            )
        self.CLIENT_YAML.write_text(yaml.safe_dump(cfg.to_dict()))

    @on(EnvironmentDelete)
    def handle_env_del(self, msg: EnvironmentDelete):
        """Handle delete from the environment (Profile) table."""
        cfg: legacy.ConfigSui = self._CONFIG_ROWS[0].configuration
        if msg.new_active:
            cfg.active_env = msg.new_active
            self._CONFIG_ROWS[0].handle_active_value_change(
                self.GroupActiveChange("name", msg.new_active)
            )
        index = next(
            (i for i, obj in enumerate(cfg.envs) if obj.alias == msg.env_context), None
        )
        cfg.envs.pop(index)
        self.CLIENT_YAML.write_text(yaml.safe_dump(cfg.to_dict()))

    @on(EditableDataTable.RowDelete)
    def group_row_delete(self, selected: EditableDataTable.RowDelete):
        """Handle delete from the EditTable."""
        self.remove_row(selected.table, selected.row_key)

    @work
    async def remove_row(self, data_table: EditableDataTable, row_key: RowKey) -> None:
        """Work for removing rows

        Args:
            data_table (EditableDataTable): The focus table (Profile or Identity)
            row_key (RowKey): Unique row key in table.
        """
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
        """dropping_row _summary_

        Args:
            from_table (EditableDataTable): The focus table (Profile or Identity)
            row_key (RowKey): Unique row key in table
            row_name (str): The name column value in the row
            active_flag (str): Active flag on row indicator

        Raises:
            NotImplementedError: If not handled by configuration section.
        """
        raise NotImplementedError(
            f"Drop for '{row_name}' in {row_key} not implemented and active is {active_flag}."
        )


class ConfigGroup(ConfigRow):

    _CG_HEADER: tuple[str, str] = ("Setting", "Target")
    _CG_EDITS: list[CellConfig] = [
        CellConfig("Setting", False, False),
        CellConfig("Target", False, False),
    ]

    def compose(self):
        yield EditableDataTable(
            self, self._CG_EDITS, disable_delete=True, id="config_group"
        )

    def validate_group_name(self, table: EditableDataTable, in_value: str) -> bool:
        """Validate that there is no same name collision."""
        coordinate = table.cursor_coordinate
        pre_value = str(table.get_cell_at(coordinate))
        if pre_value == in_value:
            pass
        elif in_value in self.configuration.group_names():
            return False
        return True

    def on_mount(self) -> None:
        self.border_title = self.name
        table: EditableDataTable = self.query_one("#config_group")
        table.add_columns(*self._CG_HEADER)
        table.focus()

    def handle_active_value_change(self, msg: ConfigRow.GroupActiveChange):
        """Handle a change of active environment or address value."""
        # Assume it is profile
        table: EditableDataTable = self.query_one("#config_group")
        coordinate = Coordinate(0, 1)
        if msg.target == "address":
            coordinate = coordinate.down()
        table.update_cell_at(coordinate, Text(msg.new_value))

    def watch_configuration(self, cfg: legacy.ConfigSui):
        """Called when a new configuration is selected."""
        if cfg:
            table: EditableDataTable = self.query_one("#config_group")
            # Empty table
            table.clear()
            # Build basic information
            table.add_row(*[Text("Active Profile"), Text(cfg.active_env)])
            table.add_row(*[Text("Active Address"), Text(cfg.active_address)])


class ConfigProfile(ConfigRow):

    _PROFILE_NAMES: set[str] = set()
    _PROFILE_COLUMN_KEYS: list[ColumnKey] = None
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

    def compose(self):
        yield Button(
            "Add", variant="primary", compact=True, id="add_profile", disabled=True
        )
        yield EditableDataTable(
            self, self._CP_EDITS, disable_delete=False, id="config_profile"
        )

    def on_mount(self) -> None:
        self.border_title = self.name
        table: EditableDataTable = self.query_one("#config_profile")
        self._PROFILE_COLUMN_KEYS = table.add_columns(*self._CP_HEADER)
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
        """Work for adding a profile (environment)"""
        new_profile: NewProfile = await self.app.push_screen_wait(
            AddProfile(self._PROFILE_NAMES)
        )
        if new_profile:
            _ = self.post_message(ConfigRow.EnvironmentAdd(new_profile))

            table: EditableDataTable = self.query_one("#config_profile")
            number = table.row_count + 1
            label = Text(str(number), style="#B0FC38 italic")
            _ = table.add_row(
                *[Text(new_profile.name), Text("No"), Text(new_profile.url)],
                label=label,
            )

            if new_profile.active:
                table.switch_active_row(
                    (1, "Yes"),
                    (0, new_profile.name),
                    self._PROFILE_COLUMN_KEYS[1],
                    set_focus=True,
                )

    def dropping_row(
        self,
        from_table: EditableDataTable,
        row_key: RowKey,
        row_name: str,
        active_flag: str,
    ) -> None:
        """Delete a profile/env row."""
        new_active_name: str = None
        # Check if the one being deleted is active
        # Do the switch if so
        if active_flag == "Yes":
            new_coord = from_table.switch_active_row(
                (0, row_name), (1, "No"), self._PROFILE_COLUMN_KEYS[1]
            )
            # new_cord = from_table.switch_active((0, row_name), (1, "No"))
            new_active_name = str(from_table.get_cell_at(new_coord))

        # Notify persist (ConfigRow)
        _ = self.post_message(ConfigRow.EnvironmentDelete(row_name, new_active_name))
        # Delete from table
        from_table.remove_row(row_key)

    def validate_profile_name(self, table: EditableDataTable, in_value: str) -> bool:
        """Validate no rename collision."""
        coordinate = table.cursor_coordinate
        pre_value = str(table.get_cell_at(coordinate))
        if pre_value == in_value:
            pass
        elif in_value in self._PROFILE_NAMES:
            return False
        return True

    @on(EditableDataTable.CellValueChange)
    def cell_change(self, cell: EditableDataTable.CellValueChange):
        """When a cell changes"""
        if cell.old_value != cell.new_value:
            if cell.cell_config.field_name == "Active":
                # Active persist is handlee by ConfigRow
                active_coord = self._switch_active(cell, self._PROFILE_COLUMN_KEYS[1])
                _ = self.post_message(
                    ConfigRow.GroupActiveChange(
                        "profile",
                        str(cell.table.get_cell_at(active_coord)),
                    )
                )
            else:
                # Get the environment name (from either Name or URL)
                tcoords = (
                    cell.coordinates
                    if cell.cell_config.field_name == "Name"
                    else cell.coordinates.left().left()
                )
                current_env: str = str(cell.table.get_cell_at(tcoords))
                # Update the client.yaml
                _ = self.post_message(
                    ConfigRow.EnvironmentChange(
                        "rename",
                        current_env,
                        cell.cell_config.field_name,
                        cell.old_value,
                        cell.new_value,
                    )
                )
                # Update the table
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
                # Update allow list and profile keys
                if cell.cell_config.field_name == "Name":
                    self._PROFILE_NAMES = self._PROFILE_NAMES - {cell.old_value} | {
                        cell.new_value
                    }

    def watch_configuration(self, cfg: legacy.ConfigSui):
        table: EditableDataTable = self.query_one("#config_profile")
        # Empty table
        table.clear()
        self._PROFILE_NAMES = set()
        self.border_title = self.name
        if cfg:
            counter = 1
            # Build content
            active_row = 0
            for profile in cfg.envs:
                self._PROFILE_NAMES.add(profile.alias)
                label = Text(str(counter), style="#B0FC38 italic")
                if profile.alias == cfg.active_env:
                    active = "Yes"
                    active_row = counter - 1
                else:
                    active = "No"
                _ = table.add_row(
                    *[Text(profile.alias), Text(active), Text(profile.rpc)],
                    label=label,
                )
                counter += 1
            # Select the active row/column
            table.move_cursor(row=active_row, column=0, scroll=True)


@dataclasses.dataclass
class IdentityBlock(dataclasses_json.DataClassJsonMixin):
    """Holds alias for base64 public key."""

    aliases: list[ProfileAlias]
    addresses: list[str]
    prvkey: list[str]


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
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )
        self._id_block: IdentityBlock = None

    def compose(self):
        yield Button(
            "Add", variant="primary", compact=True, disabled=True, id="add_identity"
        )
        yield EditableDataTable(
            self, self._CI_EDITS, disable_delete=False, id="config_identities"
        )

    def on_mount(self) -> None:
        self.border_title = self.name
        table: EditableDataTable = self.query_one("#config_identities")
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
        alias_list = [x.alias for x in self._id_block.aliases]
        new_ident: NewIdentity | None = await self.app.push_screen_wait(
            AddIdentity(alias_list)
        )

        if new_ident:
            # Generate the new key based on user input
            mnem, addy, prfkey, prfalias = ProfileGroup.new_keypair_parts(
                of_keytype=new_ident.key_scheme,
                word_counts=new_ident.word_count,
                derivation_path=new_ident.derivation_path,
                alias=new_ident.alias,
                alias_list=alias_list,
            )
            # Update the table
            table: EditableDataTable = self.query_one("#config_identities")
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
            # Add to _id_block
            self._id_block.addresses.append(addy)
            self._id_block.aliases.append(prfalias)
            self._id_block.prvkey.append(prfkey.private_key_base64)
            # Settle active
            if new_ident.active:
                coord: Coordinate = (
                    table.switch_active_row(
                        (1, "Yes"),
                        (0, new_ident.alias),
                        self._CI_COLUMN_KEYS[1],
                        set_focus=True,
                    )
                    .right()
                    .right()
                    .right()
                )

                addy = str(table.get_cell_at(coord))
                _ = self.post_message(
                    ConfigRow.GroupActiveChange(
                        "address",
                        addy,
                    )
                )

            # Persist updated aliases
            self.CLIENT_ALIAS.write_text(
                json.dumps([x.to_dict() for x in self._id_block.aliases], indent=2),
                encoding="utf8",
            )
            # Persist updated private Keys
            self.CLIENT_KEYS.write_text(
                json.dumps(self._id_block.prvkey, indent=2), encoding="utf8"
            )
            _ = await self.app.push_screen_wait(NewKey(mnem, prfkey.private_key_base64))

    def dropping_row(
        self,
        from_table: EditableDataTable,
        row_key: RowKey,
        row_name: str,
        active_flag: str,
    ) -> None:
        # Find the index
        a_index = None
        for index, alias in enumerate(self._id_block.aliases):
            if alias.alias == row_name:
                a_index = index
                # Pop the address and private key
                self._id_block.addresses.pop(a_index)
                self._id_block.prvkey.pop(a_index)
        if not a_index:
            raise ValueError(f"Unable to find alias {row_name} in identities")
        # Pop the alias
        self._id_block.aliases.pop(a_index)
        # Handle active switch
        if active_flag == "Yes":
            coord = (
                from_table.switch_active_row(
                    (0, row_name), (1, "No"), self._CI_COLUMN_KEYS[1]
                )
                .right()
                .right()
                .right()
            )
            addy = str(from_table.get_cell_at(coord))
            _ = self.post_message(
                ConfigRow.GroupActiveChange(
                    "address",
                    addy,
                )
            )

        # Delete row from table
        from_table.remove_row(row_key)
        # Persist updated aliases
        self.CLIENT_ALIAS.write_text(
            json.dumps([x.to_dict() for x in self._id_block.aliases], indent=2),
            encoding="utf8",
        )
        # Persist updated private Keys
        self.CLIENT_KEYS.write_text(
            json.dumps(self._id_block.prvkey, indent=2), encoding="utf8"
        )

    def validate_alias_name(self, table: EditableDataTable, in_value: str) -> bool:
        """Validate no rename collision."""
        coordinate = table.cursor_coordinate
        pre_value = str(table.get_cell_at(coordinate))
        if pre_value == in_value:
            pass
        elif in_value in [x.alias for x in self._id_block.aliases]:
            return False
        return True

    @on(EditableDataTable.CellValueChange)
    def cell_change(self, cell: EditableDataTable.CellValueChange):
        """When a cell edit occurs"""
        if cell.old_value != cell.new_value:
            if cell.cell_config.field_name == "Alias":
                # With alias name change, update the _id_block and write
                # to sui.aliases
                for pfa in self._id_block.aliases:
                    if pfa.alias == cell.old_value:
                        pfa.alias = cell.new_value
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
                self.CLIENT_ALIAS.write_text(
                    json.dumps([x.to_dict() for x in self._id_block.aliases], indent=2),
                    encoding="utf8",
                )

            elif cell.cell_config.field_name == "Active":
                new_coord = (
                    self._switch_active(cell, self._CI_COLUMN_KEYS[1])
                    .right()
                    .right()
                    .right()
                )
                addy = str(cell.table.get_cell_at(new_coord))
                _ = self.post_message(
                    ConfigRow.GroupActiveChange(
                        "address",
                        addy,
                    )
                )

    def watch_configuration(self, cfg: legacy.ConfigSui):
        if not cfg:
            return
        _alias_cache: list[legacy.ProfileAlias] = [
            legacy.ProfileAlias.from_dict(x)
            for x in json.loads(self.CLIENT_ALIAS.read_text(encoding="utf8"))
        ]
        _prv_keys: list[str] = json.loads(self.CLIENT_KEYS.read_text(encoding="utf8"))
        _addy_list: list[str] = []
        for prvkey in _prv_keys:
            _kp = keypair_from_keystring(prvkey).to_bytes()
            digest = _kp[0:33] if _kp[0] == 0 else _kp[0:34]
            pubkey = base64.b64encode(digest).decode()
            alias = next(
                filter(lambda pa: pa.public_key_base64 == pubkey, _alias_cache), False
            )
            if alias:
                _addy_list.append(
                    format(f"0x{hashlib.blake2b(digest, digest_size=32).hexdigest()}")
                )
            else:
                raise ValueError(f"{pubkey} not found in alias list")

        self._id_block = IdentityBlock(_alias_cache, _addy_list, _prv_keys)
        table: EditableDataTable = self.query_one("#config_identities")  # type: ignore
        # Empty table
        table.clear()

        # Build content
        active_row = 0
        for idx, alias in enumerate(self._id_block.aliases):
            label = Text(str(idx + 1), style="#B0FC38 italic")
            addy = self._id_block.addresses[idx]
            if addy == cfg.active_address:
                active = "Yes"
                active_row = idx
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
        table.move_cursor(row=active_row, column=0, scroll=True)


class MystenCfgScreen(Screen[None]):
    """."""

    DEFAULT_CSS = """
    $background: black;
    $surface: black;

    #mconfig-header {
        background:blue;
    }
    #mapp-grid {
        layout: grid;
        grid-size: 1;
        grid-columns: 1fr;
        grid-rows: 1fr;
    }    
    #top-right {
        height: 100%;
        background: $panel;
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
    ]

    def __init__(
        self,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ):
        self.config_sections = [
            ("Groups", ConfigGroup),
            ("Environment", ConfigProfile),
            ("Identities", ConfigIdentities),
        ]
        super().__init__(name, id, classes)

    def compose(self) -> ComposeResult:
        yield Header(id="mconfig-header")
        self.title = "Mysten Client Configuration: (ctrl+f to select)"
        with Grid(id="mapp-grid"):
            # yield ConfigSelection(id="config-list")
            with Vertical(id="top-right"):
                for section_name, section_class in self.config_sections:
                    yield section_class(name=section_name)
        yield Footer()

    async def action_select(self) -> None:
        self.select_configuration()

    @work()
    async def select_configuration(self) -> None:
        """Run selection modal dialog."""

        def check_selection(selected: Path | None) -> None:
            """Called when ConfigPicker is dismissed."""
            if selected:
                self.title = f"Mysten Client Configuration: {selected}"
                ConfigRow.load_sui_config(selected)

        self.app.push_screen(ConfigPicker("client.yaml"), check_selection)
