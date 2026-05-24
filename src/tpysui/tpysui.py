import logging

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import ContentSwitcher, Footer

from .version import __version__
from .settings import Settings, load_settings
from .services.base import SuiService
from .services.faux_service import FauxSuiService
from .widgets.sidebar import Sidebar
from .widgets.active_state_bar import ActiveStateBar
from .screens.config_screen import ConfigScreen
from .screens.reads_screen import ReadsScreen
from .screens.writes_screen import WritesScreen
from .screens.tx_screen import TxScreen
from .screens.uci_screen import UciScreen


class TpysuiApp(App):
    CSS_PATH = "tpysui.tcss"
    TITLE = "tpysui"
    SUB_TITLE = __version__
    BINDINGS = [("ctrl+q", "quit", "Quit")]

    settings: Settings
    service: SuiService

    def compose(self) -> ComposeResult:
        yield ActiveStateBar(id="active-state-bar")
        with Horizontal(id="main-row"):
            yield Sidebar(id="sidebar")
            with ContentSwitcher(initial="screen-config", id="content"):
                yield ConfigScreen(id="screen-config")
                yield ReadsScreen(id="screen-reads")
                yield WritesScreen(id="screen-writes")
                yield TxScreen(id="screen-tx")
                yield UciScreen(id="screen-uci")
        yield Footer()

    async def on_mount(self) -> None:
        self.settings = load_settings()
        self.service = self._build_service()
        bar = self.query_one(ActiveStateBar)
        bar.set_state(await self.service.active_state())
        self.query_one(ConfigScreen).load()

    def _build_service(self) -> SuiService:
        if self.settings.faux_mode:
            return FauxSuiService()
        raise NotImplementedError("Real pysui service ships in Sprint 3")

    def on_sidebar_area_selected(self, msg: "Sidebar.AreaSelected") -> None:
        self.query_one(ContentSwitcher).current = msg.screen_id


def main() -> None:
    logging.basicConfig(
        filename="tpysui.log",
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    TpysuiApp().run()
