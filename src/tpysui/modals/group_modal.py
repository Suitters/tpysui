#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Button, Checkbox, Collapsible, Input, Label, RadioButton, RadioSet, Select, Static

from ..constants import (
    GQL_STANDARD_PROFILES, GRPC_STANDARD_PROFILES,
    SUI_GQL_GROUP, SUI_GRPC_GROUP,
)
from ..services.base import GroupProtocol
from ..utils.sui_cli import load_cli_config

_TYPE_GQL    = "gql"
_TYPE_GRPC   = "grpc"
_TYPE_CUSTOM = "custom"


class GroupModal(ModalScreen[dict | None]):
    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+s", "submit", "Create"),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._cli = load_cli_config()
        self._selected_type = _TYPE_GQL

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
          with VerticalScroll():
            yield Static("Create Group", id="dialog-title")
            with Vertical(classes="radio-box"):
                with RadioSet(id="type-select"):
                    yield RadioButton("Standard GraphQL", id="radio-gql", value=True)
                    yield RadioButton("Standard gRPC",    id="radio-grpc")
                    yield RadioButton("Custom",           id="radio-custom")

            with Vertical(id="std-section", classes="section"):
                yield Label("Name:", classes="field-label")
                yield Static(SUI_GQL_GROUP, id="std-name")
                with Collapsible(title="Profiles", collapsed=True, id="col-profiles"):
                    with VerticalScroll(id="std-profile-list", classes="list-scroll"):
                        for name, url in GQL_STANDARD_PROFILES:
                            yield Checkbox(f"{name}  {url}", value=True, name=f"profile:{name}:{url}")
                if self._cli.envs:
                    with Collapsible(title="CLI Envs", collapsed=True, id="col-cli-envs"):
                        with VerticalScroll(id="cli-env-list", classes="list-scroll"):
                            for env in self._cli.envs:
                                yield Checkbox(f"{env.alias}  {env.url}", value=False,
                                               name=f"profile:{env.alias}:{env.url}")
                if self._cli.keys:
                    with Collapsible(title="CLI Keys", collapsed=True, id="col-cli-keys"):
                        with VerticalScroll(id="cli-key-list", classes="list-scroll"):
                            for key in self._cli.keys:
                                yield Checkbox(f"{key.alias}", value=False,
                                               name=f"key:{key.alias}:{key.public_key}")

            with Vertical(id="custom-section", classes="section"):
                yield Label("Group name:", classes="field-label")
                yield Input(placeholder="my_group", id="custom-name")
                yield Label("Protocol:", classes="field-label")
                yield Select(
                    [(p.value, p) for p in GroupProtocol],
                    value=GroupProtocol.GRAPHQL,
                    id="custom-protocol",
                )

            with Horizontal(id="buttons"):
                yield Button("Create", variant="success", id="btn-create")
                yield Button("Cancel", variant="primary",  id="btn-cancel")

    def on_collapsible_expanded(self, event: Collapsible.Expanded) -> None:
        for col in self.query(Collapsible):
            if col is not event.collapsible:
                col.collapsed = True

    async def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        idx = event.index
        if idx == 0:
            self._selected_type = _TYPE_GQL
            await self._rebuild_std_profiles(GQL_STANDARD_PROFILES, SUI_GQL_GROUP)
        elif idx == 1:
            self._selected_type = _TYPE_GRPC
            await self._rebuild_std_profiles(GRPC_STANDARD_PROFILES, SUI_GRPC_GROUP)
        else:
            self._selected_type = _TYPE_CUSTOM
        self.query_one("#std-section").display    = (self._selected_type != _TYPE_CUSTOM)
        self.query_one("#custom-section").display = (self._selected_type == _TYPE_CUSTOM)

    async def _rebuild_std_profiles(
        self, profiles: list[tuple[str, str]], group_name: str
    ) -> None:
        self.query_one("#std-name", Static).update(group_name)
        container = self.query_one("#std-profile-list")
        await container.remove_children()
        for name, url in profiles:
            await container.mount(
                Checkbox(f"{name}  {url}", value=True, name=f"profile:{name}:{url}")
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "btn-create":
            self.action_submit()
        else:
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_submit(self) -> None:
        if self._selected_type == _TYPE_CUSTOM:
            name = self.query_one("#custom-name", Input).value.strip()
            if not name:
                self.notify("Group name is required", severity="error")
                return
            raw = self.query_one("#custom-protocol", Select).value
            protocol = raw if isinstance(raw, GroupProtocol) else GroupProtocol.GRAPHQL
            self.dismiss({"name": name, "protocol": protocol, "profiles": [], "keys": []})
            return

        name = SUI_GQL_GROUP if self._selected_type == _TYPE_GQL else SUI_GRPC_GROUP
        protocol = GroupProtocol.GRAPHQL if self._selected_type == _TYPE_GQL else GroupProtocol.GRPC

        profiles: list[dict] = []
        keys: list[dict] = []
        for cb in self.query(Checkbox):
            if not cb.value:
                continue
            parts = (cb.name or "").split(":", 2)
            if len(parts) == 3:
                kind, a, b = parts
                if kind == "profile":
                    profiles.append({"name": a, "url": b})
                elif kind == "key":
                    keys.append({"alias": a, "public_key": b})

        self.dismiss({"name": name, "protocol": protocol, "profiles": profiles, "keys": keys})
