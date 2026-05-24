import asyncio
from pathlib import Path

from .base import SuiService, GroupInfo, GroupProtocol, ProfileInfo, AddressInfo, ActiveState


_GROUPS: list[GroupInfo] = [
    GroupInfo(name="sui_config", protocol=GroupProtocol.GRAPHQL, profile_count=3, address_count=4, is_active=True),
    GroupInfo(name="devnet_cfg", protocol=GroupProtocol.GRPC,    profile_count=2, address_count=3, is_active=False),
]

_PROFILES: dict[str, list[ProfileInfo]] = {
    "sui_config": [
        ProfileInfo(name="mainnet",    group_name="sui_config", url="https://sui-mainnet.mystenlabs.com/graphql", is_active=True),
        ProfileInfo(name="testnet",    group_name="sui_config", url="https://sui-testnet.mystenlabs.com/graphql", is_active=False),
        ProfileInfo(name="devnet",     group_name="sui_config", url="https://sui-devnet.mystenlabs.com/graphql",  is_active=False),
    ],
    "devnet_cfg": [
        ProfileInfo(name="devnet_node", group_name="devnet_cfg", url="https://fullnode.devnet.sui.io:443",        is_active=True),
        ProfileInfo(name="localnet",    group_name="devnet_cfg", url="http://localhost:9000",                     is_active=False),
    ],
}

_ADDRESSES: dict[str, list[AddressInfo]] = {
    "sui_config": [
        AddressInfo(alias="alice", address="0x" + "01" * 32, group_name="sui_config", key_scheme="ed25519",   is_active=True),
        AddressInfo(alias="bob",   address="0x" + "02" * 32, group_name="sui_config", key_scheme="ed25519",   is_active=False),
        AddressInfo(alias="carol", address="0x" + "03" * 32, group_name="sui_config", key_scheme="secp256k1", is_active=False),
        AddressInfo(alias="dave",  address="0x" + "04" * 32, group_name="sui_config", key_scheme="ed25519",   is_active=False),
    ],
    "devnet_cfg": [
        AddressInfo(alias="dev_main", address="0x" + "05" * 32, group_name="devnet_cfg", key_scheme="ed25519",   is_active=True),
        AddressInfo(alias="test1",    address="0x" + "06" * 32, group_name="devnet_cfg", key_scheme="ed25519",   is_active=False),
        AddressInfo(alias="test2",    address="0x" + "07" * 32, group_name="devnet_cfg", key_scheme="secp256k1", is_active=False),
    ],
}

_ACTIVE_STATE = ActiveState(
    config_path=str(Path.home() / ".tpysui" / "faux" / "sui_config.json"),
    group_name="sui_config",
    profile_name="mainnet",
    address_alias="alice",
    address="0x" + "01" * 32,
)


class FauxSuiService(SuiService):
    async def active_state(self) -> ActiveState:
        await asyncio.sleep(0.05)
        return _ACTIVE_STATE

    async def list_groups(self) -> list[GroupInfo]:
        await asyncio.sleep(0.05)
        return list(_GROUPS)

    async def list_profiles(self, group_name: str) -> list[ProfileInfo]:
        await asyncio.sleep(0.05)
        return list(_PROFILES.get(group_name, []))

    async def list_addresses(self, group_name: str) -> list[AddressInfo]:
        await asyncio.sleep(0.05)
        return list(_ADDRESSES.get(group_name, []))
