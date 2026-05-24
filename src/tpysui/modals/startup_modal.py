from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Input, Label, Static

from ..constants import SUI_GQL_GROUP, SUI_GRPC_GROUP
from ..services.base import GroupProtocol


class StartupModal(ModalScreen[dict | None]):
    BINDINGS = [("escape", "cancel", "Cancel")]
    DEFAULT_CSS = """
    StartupModal { align: center middle; }
    StartupModal #dialog {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 1 2;
    }
    StartupModal #dialog-title { text-style: bold; margin-bottom: 1; }
    StartupModal #new-section { display: none; height: auto; }
    StartupModal #open-section { display: none; height: auto; }
    StartupModal .field-label { color: $text-muted; margin-top: 1; }
    StartupModal #choice-buttons { align: center middle; height: auto; margin-top: 1; }
    StartupModal #action-buttons { align: right middle; height: auto; margin-top: 1; }
    StartupModal Button { margin: 0 1; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Static("Welcome to tpysui", id="dialog-title")
            with Horizontal(id="choice-buttons"):
                yield Button("New Config", variant="success", id="btn-new")
                yield Button("Open Existing", variant="primary", id="btn-open")
            with Vertical(id="new-section"):
                yield Label("Config folder:", classes="field-label")
                yield Input(placeholder="~/path/to/config/folder", id="new-folder")
                yield Label("Initial groups:", classes="field-label")
                yield Checkbox("GraphQL group", value=True, id="chk-gql")
                yield Checkbox("gRPC group", value=False, id="chk-grpc")
                with Horizontal(id="action-buttons"):
                    yield Button("Create", variant="success", id="btn-create")
                    yield Button("Back", id="btn-back-new")
            with Vertical(id="open-section"):
                yield Label("Path to PysuiConfig.json:", classes="field-label")
                yield Input(placeholder="~/path/to/PysuiConfig.json", id="open-path")
                with Horizontal(id="action-buttons"):
                    yield Button("Open", variant="success", id="btn-open-confirm")
                    yield Button("Back", id="btn-back-open")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        bid = event.button.id
        if bid == "btn-new":
            self.query_one("#choice-buttons").display = False
            self.query_one("#new-section").display = True
        elif bid == "btn-open":
            self.query_one("#choice-buttons").display = False
            self.query_one("#open-section").display = True
        elif bid in ("btn-back-new", "btn-back-open"):
            self.query_one("#choice-buttons").display = True
            self.query_one("#new-section").display = False
            self.query_one("#open-section").display = False
        elif bid == "btn-create":
            self._submit_new()
        elif bid == "btn-open-confirm":
            self._submit_open()

    def _submit_new(self) -> None:
        folder = self.query_one("#new-folder", Input).value.strip()
        if not folder:
            self.notify("Folder path is required", severity="error")
            return
        gql = self.query_one("#chk-gql", Checkbox).value
        grpc = self.query_one("#chk-grpc", Checkbox).value
        if not gql and not grpc:
            self.notify("Select at least one group type", severity="error")
            return
        init_groups: list[dict] = []
        first = True
        if gql:
            init_groups.append({"name": SUI_GQL_GROUP, "protocol": GroupProtocol.GRAPHQL, "make_active": first})
            first = False
        if grpc:
            init_groups.append({"name": SUI_GRPC_GROUP, "protocol": GroupProtocol.GRPC, "make_active": first})
        self.dismiss({"action": "new", "folder": folder, "init_groups": init_groups})

    def _submit_open(self) -> None:
        path = self.query_one("#open-path", Input).value.strip()
        if not path:
            self.notify("Path is required", severity="error")
            return
        self.dismiss({"action": "open", "path": path})

    def action_cancel(self) -> None:
        self.dismiss(None)
