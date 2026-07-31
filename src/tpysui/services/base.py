#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from textual.message import Message


class GroupProtocol(str, Enum):
    GRAPHQL = "GraphQL"
    GRPC = "gRPC"
    OTHER = "Other"


@dataclass(frozen=True)
class GroupInfo:
    name: str
    protocol: GroupProtocol
    profile_count: int
    address_count: int
    is_active: bool


@dataclass(frozen=True)
class ProfileInfo:
    name: str
    group_name: str
    url: str
    is_active: bool
    network_type: str


@dataclass(frozen=True)
class AddressInfo:
    alias: str
    address: str
    group_name: str
    key_scheme: str
    is_active: bool


@dataclass(frozen=True)
class ActiveState:
    config_path: str | None
    group_name: str | None
    profile_name: str | None
    profile_url: str | None
    address_alias: str | None
    address: str | None


@dataclass(frozen=True)
class ObjectSummaryInfo:
    object_id: str
    object_type: str
    digest: str = ""
    version: str = ""


@dataclass(frozen=True)
class GasObjectInfo:
    object_id: str
    balance: str
    digest: str = ""
    version: str = ""


@dataclass(frozen=True)
class ChainInfo:
    chain_id: str
    epoch: str
    reference_gas_price: str
    validator_count: str


@dataclass(frozen=True)
class ReadResult:
    json_str: str | None
    cursor: bytes | None
    error: str | None


@dataclass(frozen=True)
class ArgInfo:
    name: str
    arg_type: str
    optional: bool = False


@dataclass(frozen=True)
class CommandInfo:
    name: str
    category: str
    args: tuple["ArgInfo", ...]
    pageable: bool


@dataclass(frozen=True)
class UtilityResultDTO:
    simulated: bool
    success: bool
    error: str | None
    digest: str | None
    gas_used: int | None
    mutated: list[str]
    created: list[str]
    deleted: list[str]
    events: list[dict]
    raw_json: str


class ActiveStateChanged(Message):
    """Posted when the active group/profile/address changes."""

    def __init__(self, state: ActiveState) -> None:
        super().__init__()
        self.state = state


class SuiService(ABC):
    @abstractmethod
    async def active_state(self) -> ActiveState: ...

    @abstractmethod
    async def list_groups(self) -> list[GroupInfo]: ...

    @abstractmethod
    async def list_profiles(self, group_name: str) -> list[ProfileInfo]: ...

    @abstractmethod
    async def list_addresses(self, group_name: str) -> list[AddressInfo]: ...

    # --- mutations ---

    @abstractmethod
    async def create_group(
        self, name: str, protocol: GroupProtocol,
        profiles: list[dict], keys: list[dict],
    ) -> GroupInfo: ...

    @abstractmethod
    async def delete_group(self, name: str) -> str: ...

    @abstractmethod
    async def set_active_group(self, name: str) -> ActiveState: ...

    @abstractmethod
    async def create_profile(
        self, group_name: str, name: str, url: str, network_type: str
    ) -> ProfileInfo: ...

    @abstractmethod
    async def update_profile(
        self, group_name: str, name: str, url: str, network_type: str
    ) -> ProfileInfo: ...

    @abstractmethod
    async def delete_profile(self, group_name: str, name: str) -> None: ...

    @abstractmethod
    async def set_active_profile(self, group_name: str, name: str) -> ActiveState: ...

    @abstractmethod
    async def generate_keypair(self, group_name: str, alias: str) -> tuple[AddressInfo, str]: ...

    @abstractmethod
    async def import_address(self, group_name: str, alias: str, private_key: str) -> AddressInfo: ...

    @abstractmethod
    async def rename_alias(
        self, group_name: str, existing_alias: str, new_alias: str,
    ) -> AddressInfo: ...

    @abstractmethod
    async def delete_address(self, group_name: str, alias: str) -> None: ...

    @abstractmethod
    async def set_active_address(self, group_name: str, alias: str) -> ActiveState: ...

    @abstractmethod
    async def get_chain_info(self) -> "ChainInfo": ...

    @abstractmethod
    async def execute_read(self, command_name: str, kwargs: dict, cursor: bytes | None) -> ReadResult: ...

    @abstractmethod
    async def get_owned_objects(self, owner: str) -> "list[ObjectSummaryInfo]": ...

    @abstractmethod
    async def get_owned_coins(self, owner: str) -> "list[ObjectSummaryInfo]": ...

    @abstractmethod
    async def get_gas_objects(self, owner: str) -> "list[GasObjectInfo]": ...

    @abstractmethod
    async def get_coin_balances(self, owner: str) -> str: ...

    @abstractmethod
    async def run_utility(
        self, name: str, args: dict, simulate: bool
    ) -> "UtilityResultDTO": ...

    @abstractmethod
    async def aclose(self) -> None: ...
