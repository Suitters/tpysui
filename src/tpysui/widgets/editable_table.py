#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Customized widgets for App."""
import dataclasses
from typing import Optional, Callable, Iterable, Any


from textual import work, events
from textual.app import ComposeResult
from textual.containers import Container
from textual.coordinate import Coordinate
from textual.geometry import Offset, Region
from textual.message import Message
from textual.screen import ModalScreen
import textual.validation as validator
from textual.widgets import DataTable, Input, Pretty
from textual.widgets.data_table import Row, ColumnKey, RowKey

from ..modals import OkPopup


class EditWidgetScreen(ModalScreen):
    """A modal screen with a single input widget."""

    CSS = """
        Input.-valid {
            border: tall $success 60%;
        }
        Input.-valid:focus {
            border: tall $success;
        }    
        Pretty {
            margin: 1 2;
        }        
        Input {
            border: solid $secondary-darken-3;
            padding: 0;

            &:focus {
                border: round $secondary;
            }
        }
    """

    def __init__(
        self,
        value: Any,
        region: Region,
        validators: validator.Validator | Iterable[validator.Validator] | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialization.

        Args:
            value (Any): the original value.
            region (Region): the region available for the input widget contents.
        """
        super().__init__(*args, **kwargs)
        self.validators = validators if validators else []
        self.value = value
        # store type to later cast the new value to the old type
        self.value_type = type(value)
        self.widget_region = region

    def compose(self) -> ComposeResult:
        yield Input(
            value=str(self.value), validators=self.validators, validate_on=["submitted"]
        )
        yield Pretty([])

    def on_mount(self) -> None:
        """Calculate and set the input widget's position and size.

        This takes into account any padding you might have set on the input
        widget, although the default padding is 0.
        """
        input = self.query_one(Input)
        input.offset = Offset(
            self.widget_region.offset.x - input.styles.padding.left - 1,
            self.widget_region.offset.y - input.styles.padding.top - 1,
        )
        input.styles.width = (
            self.widget_region.width
            + input.styles.padding.left
            + input.styles.padding.right
            # include the borders _and_ the cursor at the end of the line
            + 3
        )
        input.styles.height = (
            self.widget_region.height
            + input.styles.padding.top
            + input.styles.padding.bottom
            # include the borders
            + 2
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Return the new value.

        The new value is cast to the original type. If that is not possible
        (e.g. you try to replace a number with a string), returns None to
        indicate that the cell should _not_ be updated.
        """
        try:
            if not event.validation_result.is_valid:
                self.query_one(Pretty).update(
                    event.validation_result.failure_descriptions
                )
            else:
                self.dismiss(self.value_type(event.value))
        except ValueError:
            self.dismiss(None)

    def _on_key(self, event: events.Key) -> None:
        """Allow escape for cancelling."""
        if event.name == "escape":
            self.dismiss(None)

        return super()._on_key(event)


@dataclasses.dataclass
class CellConfig:
    field_name: str
    editable: Optional[bool] = True
    inline: Optional[bool] = False
    validators: validator.Validator | Iterable[validator.Validator] | None = None
    dialog: Optional[Callable] = None


class EditableDataTable(DataTable):
    """A datatable where you can edit cells."""

    BINDINGS = [("ctrl+e", "edit", "Edit Cell")]

    class CellValueChange(Message):

        def __init__(
            self,
            table: "EditableDataTable",
            cell_config: CellConfig,
            coordinates: Coordinate,
            old_value: str,
            new_value: str,
        ):
            self.table = table
            self.cell_config: CellConfig = cell_config
            self.coordinates: Coordinate = coordinates
            self.old_value: str = old_value
            self.new_value: str = new_value
            super().__init__()

    class RowDelete(Message):

        def __init__(self, table: "EditableDataTable", row_key: RowKey):
            super().__init__()
            self.table = table
            self.row_key = row_key

    def __init__(
        self,
        owner: Container,
        edit_config: list[CellConfig],
        disable_delete: bool,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.owner = owner
        self.delete_disabled = disable_delete
        self.delete_button = "[bold red]Delete"
        self.edit_config = edit_config
        self.delte_column = 0

    def add_columns(self, *labels) -> list[ColumnKey]:
        keys = super().add_columns(*labels)
        if not self.delete_disabled:
            self.delete_column = len(keys)
            super().add_column("", key="delete")
        return keys

    def add_row(self, *cells, height=1, key=None, label=None) -> RowKey:
        cells = [*cells]
        if not self.delete_disabled:
            cells.append(self.delete_button)
        rkey = super().add_row(*tuple(cells), height=height, key=key, label=label)
        return rkey

    def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        if event.value == self.delete_button:
            self.post_message(self.RowDelete(event.data_table, event.cell_key.row_key))

    async def action_edit(self) -> None:
        if self.ordered_rows:
            coords = self.cursor_coordinate
            # Avoid the 'delete' button
            if coords.column != self.delete_column:
                edit_cfg = self.edit_config[coords.column]
                if edit_cfg.editable == False:
                    return
                if edit_cfg.field_name == "Active" and self.row_count == 1:
                    self.app.push_screen(
                        OkPopup("[red]Can not change Active state for only row")
                    )
                else:
                    if edit_cfg.inline:
                        self.edit_cell(coordinate=coords, cfg=edit_cfg)
                    elif edit_cfg.dialog:
                        self.edit_dialog(coordinate=coords, cfg=edit_cfg)

    @work()
    async def edit_dialog(self, coordinate: Coordinate, cfg: CellConfig) -> None:
        old_value = str(self.get_cell_at(coordinate))
        new_value = await self.app.push_screen_wait(cfg.dialog())
        if new_value is not None:
            self.post_message(
                self.CellValueChange(self, cfg, coordinate, old_value, new_value)
            )

    @work()
    async def edit_cell(self, coordinate: Coordinate, cfg: CellConfig) -> None:
        """Edit cell contents.

        Args:
            coordinate (Coordinate): the coordinate of the cell to update.
            cfg (CellConfig): the configuration of the cell
        """
        region = self._get_cell_region(coordinate)
        # the region containing the cell contents, without padding
        contents_region = Region(
            region.x + self.cell_padding,
            region.y,
            region.width - 2 * self.cell_padding,
            region.height,
        )
        absolute_offset = self.screen.get_offset(self)
        absolute_region = contents_region.translate(absolute_offset)
        old_value_cell = self.get_cell_at(coordinate)

        new_value = await self.app.push_screen_wait(
            EditWidgetScreen(
                value=old_value_cell,
                region=absolute_region,
                validators=cfg.validators,
            )
        )
        if new_value is not None:
            self.post_message(
                self.CellValueChange(
                    self, cfg, coordinate, str(old_value_cell), str(new_value)
                )
            )

    def row_with_value(self, row_cell: int, value: str) -> list[Row]:
        """row_with_value Retrieves a row that meets the row cell (column) and value criteria.

        Args:
            row_cell (int): The column index in the row to retrieve current value
            value (str): The value that should match the contents of said column index

        Returns:
            list[Row]: List of Rows that satisfy the criteria.
        """

        def has_value(in_rowc: Row):
            """."""
            if str(self.get_row(in_rowc.key)[row_cell]) == value:
                return True
            else:
                return False

        return list(filter(has_value, self.ordered_rows))

    def switch_active_row(
        self,
        from_t: tuple[int, str],
        to_t: tuple[int, str],
        c_key: ColumnKey,
        set_focus: Optional[bool] = False,
    ) -> Coordinate:
        """."""
        from_row = self.row_with_value(*from_t)
        to_row = self.row_with_value(*to_t)
        active_coordinate: Coordinate = None
        if from_row:
            self.update_cell(from_row[0].key, c_key, "No", update_width=False)
        if to_row:
            self.update_cell(to_row[0].key, c_key, "Yes", update_width=True)
            active_coordinate = self.get_cell_coordinate(to_row[0].key, c_key)
        if set_focus:
            self.focus()
            if active_coordinate:
                self.move_cursor(row=active_coordinate.row, column=0)
        return active_coordinate.left()

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        """Check if an action may run."""
        if action in ["edit"] and self.row_count == 0:
            return None
        return True
