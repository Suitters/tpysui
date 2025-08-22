#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Termpysui TUI Application."""

import logging

logging.basicConfig(
    filename="tpysui.log",
    filemode="w",
    encoding="utf-8",
    format="%(asctime)s %(module)s %(levelname)s %(message)s",
    level=logging.DEBUG,
)

from textual.app import App
from textual.binding import Binding
from .screens import PyCfgScreen, MystenCfgScreen


class TermPysuiApp(App):
    """A Textual pysui app to manage configurations."""

    BINDINGS = [
        Binding("c", "switch_mode('pycfg')", "Pysui Configs", show=False),
        Binding("m", "switch_mode('scfgs')", "Mysten Sui Configs", show=False),
    ]
    MODES = {
        "pycfg": lambda: PyCfgScreen(),
        "scfgs": lambda: MystenCfgScreen(),
    }

    def on_mount(self) -> None:
        self.switch_mode("pycfg")


def main():
    """
    main Entry point
    """
    app = TermPysuiApp()
    app.run()


if __name__ == "__main__":
    main()
