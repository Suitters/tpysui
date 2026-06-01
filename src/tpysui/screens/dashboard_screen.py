#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""DashboardScreen — Wallet overview: chain info, gas, owned objects, coin balances."""

from __future__ import annotations

import asyncio
from typing import Any

from textual import work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import ListItem, ListView, Static, TextArea

from ..services.base import ActiveState


def _fmt_id(id_str: str) -> str:
    if id_str.startswith("0x") and len(id_str) > 14:
        return f"{id_str[:10]}...{id_str[-4:]}"
    return id_str


class DashboardScreen(Widget):
    """Area 1 — Wallet Dashboard."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._last_state: ActiveState | None = None
        self._pending_refresh: bool = False

    def compose(self) -> ComposeResult:
        with Vertical(id="dashboard_body"):
            with Horizontal(id="chain_strip"):
                yield Static("Chain: —", id="dash_chain_id")
                yield Static("│", classes="dash_sep")
                yield Static("Epoch: —", id="dash_epoch")
                yield Static("│", classes="dash_sep")
                yield Static("Ref Gas: —", id="dash_refgas")
                yield Static("│", classes="dash_sep")
                yield Static("Validators: —", id="dash_validators")
            with Horizontal(id="dashboard_panels"):
                with Vertical(id="dash_gas_pane", classes="dash_pane"):
                    yield Static("Gas Objects <0x2::sui::SUI>", classes="dash_pane_title")
                    yield ListView(id="gas_list")
                with Vertical(id="dash_obj_pane", classes="dash_pane"):
                    yield Static("Owned Objects (not incl. gas)", classes="dash_pane_title")
                    yield ListView(id="obj_list")
                with Vertical(id="dash_bal_pane", classes="dash_pane"):
                    yield Static("Coin Balances", classes="dash_pane_title")
                    yield TextArea("", id="bal_text", language="json", read_only=True)

    async def on_show(self) -> None:
        if self._last_state is None:
            if not hasattr(self.app, "service"):
                return
            state = await self.app.service.active_state()  # type: ignore[attr-defined]
            self._last_state = state
            self._load_chain()
            if state.address:
                self._load_address_data(state.address)
        elif self._pending_refresh:
            self._pending_refresh = False
            self._load_chain()
            if self._last_state.address:
                self._load_address_data(self._last_state.address)

    def notify_state_changed(self, state: ActiveState) -> None:
        self._last_state = state
        if self.display:
            self._load_chain()
            if state.address:
                self._load_address_data(state.address)
        else:
            self._pending_refresh = True

    @work(exclusive=True, group="dash_chain", exit_on_error=False)
    async def _load_chain(self) -> None:
        info = await self.app.service.get_chain_info()  # type: ignore[attr-defined]
        self.query_one("#dash_chain_id", Static).update(f"Chain: {info.chain_id}")
        self.query_one("#dash_epoch", Static).update(f"Epoch: {info.epoch}")
        self.query_one("#dash_refgas", Static).update(f"Ref Gas: {info.reference_gas_price}")
        self.query_one("#dash_validators", Static).update(f"Validators: {info.validator_count}")

    @work(exclusive=True, group="dash_address", exit_on_error=False)
    async def _load_address_data(self, address: str) -> None:
        gas_objects, owned_objects, bal_json = await asyncio.gather(
            self.app.service.get_gas_objects(address),  # type: ignore[attr-defined]
            self.app.service.get_owned_objects(address),  # type: ignore[attr-defined]
            self.app.service.get_coin_balances(address),  # type: ignore[attr-defined]
        )

        gas_list = self.query_one("#gas_list", ListView)
        obj_list = self.query_one("#obj_list", ListView)
        bal_text = self.query_one("#bal_text", TextArea)

        await gas_list.clear()
        await obj_list.clear()

        gas_ids: set[str] = set()
        for gas_obj in gas_objects:
            gas_ids.add(gas_obj.object_id)
            try:
                sui_val = f"{int(gas_obj.balance) / 1_000_000_000:.4f} SUI"
            except Exception:
                sui_val = gas_obj.balance
            item = ListItem(
                Horizontal(
                    Static(_fmt_id(gas_obj.object_id), classes="gas-item-id"),
                    Static(sui_val, classes="gas-item-bal"),
                )
            )
            item.tooltip = (
                f"Digest:    {gas_obj.digest}\n"
                f"Version:   {gas_obj.version}\n"
                f"Object ID: {gas_obj.object_id}"
            )
            await gas_list.append(item)

        for obj in owned_objects:
            if obj.object_id not in gas_ids:
                item = ListItem(Static(_fmt_id(obj.object_id)))
                item.tooltip = (
                    f"Digest:    {obj.digest}\n"
                    f"Version:   {obj.version}\n"
                    f"Object ID: {obj.object_id}\n"
                    f"Type:      {obj.object_type}"
                )
                await obj_list.append(item)

        bal_text.load_text(bal_json)
