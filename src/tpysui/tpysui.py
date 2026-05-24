import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import ContentSwitcher, Footer

from .version import __version__
from .settings import Settings, load_settings, save_settings
from .services.base import ActiveStateChanged, SuiService
from .services.faux_service import FauxSuiService
from .widgets.sidebar import Sidebar
from .widgets.active_state_bar import ActiveStateBar
from .screens.config_screen import ConfigScreen
from .screens.reads_screen import ReadsScreen
from .screens.writes_screen import WritesScreen
from .screens.tx_screen import TxScreen
from .screens.uci_screen import UciScreen


def _upsert_known(settings: Settings, path: str) -> None:
    existing = [k["path"] for k in settings.known_configs]
    if path not in existing:
        settings.known_configs.append({"path": path})


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
        if self.settings.faux_mode:
            self.service = FauxSuiService()
            self.query_one(ActiveStateBar).set_state(await self.service.active_state())
            self.query_one(ConfigScreen).load()
            return
        cfg_path = self.settings.default_config_path
        if cfg_path and (Path(cfg_path) / "PysuiConfig.json").exists():
            from pysui import PysuiConfiguration
            from .services.real_service import RealSuiService
            config = PysuiConfiguration(from_cfg_path=cfg_path)
            await self._init_real_service(config)
        else:
            from .modals.startup_modal import StartupModal
            self.push_screen(StartupModal(), self._on_startup_result)

    async def _init_real_service(self, config: object) -> None:
        from .services.real_service import RealSuiService
        self.service = RealSuiService(config)
        self.query_one(ActiveStateBar).set_state(await self.service.active_state())
        self.query_one(ConfigScreen).load()

    async def _on_startup_result(self, result: dict | None) -> None:
        if result is None:
            self.exit()
            return
        from pysui import PysuiConfiguration
        from .services.base import GroupProtocol
        if result["action"] == "new":
            folder = Path(result["folder"]).expanduser()
            pysui_groups = [
                {
                    "name": g["name"],
                    "graphql_from_sui": g["protocol"] == GroupProtocol.GRAPHQL,
                    "grpc_from_sui": g["protocol"] == GroupProtocol.GRPC,
                    "make_active": g["make_active"],
                }
                for g in result["init_groups"]
            ]
            config = PysuiConfiguration.initialize_config(
                in_folder=folder,
                init_groups=pysui_groups,
            )
            config.save()
        else:
            config = PysuiConfiguration(from_cfg_path=result["path"])
        self.settings.default_config_path = config.config
        _upsert_known(self.settings, config.config)
        save_settings(self.settings)
        await self._init_real_service(config)

    def on_sidebar_area_selected(self, msg: "Sidebar.AreaSelected") -> None:
        self.query_one(ContentSwitcher).current = msg.screen_id

    def on_active_state_changed(self, msg: "ActiveStateChanged") -> None:
        self.query_one(ActiveStateBar).set_state(msg.state)


def main() -> None:
    logging.basicConfig(
        filename="tpysui.log",
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    TpysuiApp().run()
