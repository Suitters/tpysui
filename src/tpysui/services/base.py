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
    address_alias: str | None
    address: str | None


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
