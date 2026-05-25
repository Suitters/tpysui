#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

import logging
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import ContentSwitcher, Footer

from .version import __version__
from .settings import Settings, load_settings, save_settings
from .services.base import ActiveStateChanged, SuiService
from .services.faux_service import FauxSuiService
from .services.taxonomy_loader import CommandEntry, load_command_registry
from .widgets.sidebar import Sidebar
from .widgets.active_state_bar import ActiveStateBar
from .screens.config_screen import ConfigScreen
from .screens.reads_screen import ReadsScreen
from .screens.writes_screen import WritesScreen
from .screens.tx_screen import TxScreen
from .screens.uci_screen import UciScreen


_AREA_LABELS = {
    "screen-config": "Config",
    "screen-reads":  "Data Reads",
    "screen-writes": "Data Writes",
    "screen-tx":     "Tx Builder",
    "screen-uci":    "UCI Dev",
}


def _upsert_known(settings: Settings, path: str) -> None:
    existing = [k["path"] for k in settings.known_configs]
    if path not in existing:
        settings.known_configs.append({"path": path})


class TpysuiApp(App):
    CSS_PATH = "styles/tpysui.tcss"
    TITLE = "tpysui"
    SUB_TITLE = __version__
    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+1", "area_1", "Config"),
        ("ctrl+2", "area_2", "Data Reads"),
        ("ctrl+3", "area_3", "Data Writes"),
        ("ctrl+4", "area_4", "Tx Builder"),
        ("ctrl+5", "area_5", "UCI Dev"),
    ]

    settings: Settings
    service: SuiService
    command_registry: dict[str, CommandEntry]

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

    async def action_quit(self) -> None:
        if hasattr(self, "service"):
            await self.service.aclose()
        self.exit()

    async def on_mount(self) -> None:
        self.query_one(ActiveStateBar).set_area("Config")
        self.settings = load_settings()
        self.command_registry = load_command_registry()
        if self.settings.faux_mode:
            self.service = FauxSuiService()
            self.query_one(ActiveStateBar).set_state(await self.service.active_state())
            self.query_one(ConfigScreen).load()
            return
        cfg_path = self.settings.default_config_path
        if cfg_path and (Path(cfg_path) / "PysuiConfig.json").exists():
            from pysui import PysuiConfiguration
            config = PysuiConfiguration(from_cfg_path=cfg_path)
            await self._init_real_service(config)
        else:
            from .modals.startup_modal import StartupModal
            self.push_screen(StartupModal(), self._on_startup_result)

    async def _init_real_service(self, config: object) -> None:
        from .services.real_service import RealSuiService
        self.service = RealSuiService(config)
        state = await self.service.active_state()
        self.query_one(ActiveStateBar).set_state(state)
        self.query_one(ConfigScreen).load()
        self.query_one(ReadsScreen).notify_state_changed(state)

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

    def _switch_area(self, screen_id: str, move_cursor: bool = True) -> None:
        self.query_one(ContentSwitcher).current = screen_id
        self.query_one(ActiveStateBar).set_area(_AREA_LABELS.get(screen_id, "Config"))
        if move_cursor:
            self.query_one(Sidebar).select_area(screen_id)

    def action_area_1(self) -> None:
        self._switch_area("screen-config")

    def action_area_2(self) -> None:
        self._switch_area("screen-reads")

    def action_area_3(self) -> None:
        self._switch_area("screen-writes")

    def action_area_4(self) -> None:
        self._switch_area("screen-tx")

    def action_area_5(self) -> None:
        self._switch_area("screen-uci")

    def on_sidebar_area_selected(self, msg: "Sidebar.AreaSelected") -> None:
        self._switch_area(msg.screen_id, move_cursor=False)

    def on_active_state_changed(self, msg: "ActiveStateChanged") -> None:
        self.query_one(ActiveStateBar).set_state(msg.state)
        self.query_one(ReadsScreen).notify_state_changed(msg.state)

    async def on_active_state_bar_config_change_requested(
        self, _: ActiveStateBar.ConfigChangeRequested
    ) -> None:
        from .modals.config_picker_modal import ConfigPickerModal

        async def on_choice(path: str | None) -> None:
            if path:
                await self._load_config(path)

        self.push_screen(ConfigPickerModal(), on_choice)

    async def on_active_state_bar_group_change_requested(
        self, _: ActiveStateBar.GroupChangeRequested
    ) -> None:
        groups = await self.service.list_groups()
        if not groups:
            return
        from .modals.chooser_modal import ChooserModal

        async def on_choice(name: str | None) -> None:
            if name:
                await self._switch_group(name)

        self.push_screen(
            ChooserModal("Switch Active Group", [g.name for g in groups]), on_choice
        )

    async def _load_config(self, path: str) -> None:
        from pysui import PysuiConfiguration
        try:
            config = PysuiConfiguration(from_cfg_path=path)
            self.settings.default_config_path = config.config
            save_settings(self.settings)
            await self._init_real_service(config)
        except Exception as e:
            self.notify(f"Failed to load config: {e}", severity="error")

    async def _switch_group(self, name: str) -> None:
        state = await self.service.set_active_group(name)
        self.query_one(ActiveStateBar).set_state(state)
        self.query_one(ConfigScreen).load()
        self.query_one(ReadsScreen).notify_state_changed(state)


def main() -> None:
    logging.basicConfig(
        filename="tpysui.log",
        level=logging.WARNING,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    TpysuiApp().run()
