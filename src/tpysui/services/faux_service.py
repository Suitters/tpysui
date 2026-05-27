#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

import asyncio
import copy
from dataclasses import replace
from pathlib import Path

from .base import (
    ActiveState, ActiveStateChanged, AddressInfo, ChainInfo, GasObjectInfo,
    GroupInfo, GroupProtocol, ObjectSummaryInfo, ProfileInfo, ReadResult, SuiService,
)

_FAKE_MNEMONIC = (
    "word1 word2 word3 word4 word5 word6 "
    "word7 word8 word9 word10 word11 word12"
)

_INIT_GROUPS: list[GroupInfo] = [
    GroupInfo(name="sui_config", protocol=GroupProtocol.GRAPHQL, profile_count=3, address_count=4, is_active=True),
    GroupInfo(name="devnet_cfg", protocol=GroupProtocol.GRPC,    profile_count=2, address_count=3, is_active=False),
]

_INIT_PROFILES: dict[str, list[ProfileInfo]] = {
    "sui_config": [
        ProfileInfo(name="mainnet",     group_name="sui_config", url="https://sui-mainnet.mystenlabs.com/graphql", is_active=True),
        ProfileInfo(name="testnet",     group_name="sui_config", url="https://sui-testnet.mystenlabs.com/graphql", is_active=False),
        ProfileInfo(name="devnet",      group_name="sui_config", url="https://sui-devnet.mystenlabs.com/graphql",  is_active=False),
    ],
    "devnet_cfg": [
        ProfileInfo(name="devnet_node", group_name="devnet_cfg", url="https://fullnode.devnet.sui.io:443", is_active=True),
        ProfileInfo(name="localnet",    group_name="devnet_cfg", url="http://localhost:9000",              is_active=False),
    ],
}

_INIT_ADDRESSES: dict[str, list[AddressInfo]] = {
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


class FauxSuiService(SuiService):
    def __init__(self) -> None:
        self._groups: list[GroupInfo] = copy.deepcopy(_INIT_GROUPS)
        self._profiles: dict[str, list[ProfileInfo]] = copy.deepcopy(_INIT_PROFILES)
        self._addresses: dict[str, list[AddressInfo]] = copy.deepcopy(_INIT_ADDRESSES)
        self._active = ActiveState(
            config_path=str(Path.home() / ".tpysui" / "faux" / "sui_config.json"),
            group_name="sui_config",
            profile_name="mainnet",
            profile_url="https://sui-mainnet.mystenlabs.com/graphql",
            address_alias="alice",
            address="0x" + "01" * 32,
        )
        self._next_idx = 8

    # --- helpers ---

    def _find_group(self, name: str) -> GroupInfo | None:
        return next((g for g in self._groups if g.name == name), None)

    def _replace_group(self, updated: GroupInfo) -> None:
        idx = next(i for i, g in enumerate(self._groups) if g.name == updated.name)
        self._groups[idx] = updated

    def _update_active(self, **kwargs) -> ActiveState:
        self._active = ActiveState(
            config_path=kwargs.get("config_path", self._active.config_path),
            group_name=kwargs.get("group_name", self._active.group_name),
            profile_name=kwargs.get("profile_name", self._active.profile_name),
            profile_url=kwargs.get("profile_url", self._active.profile_url),
            address_alias=kwargs.get("address_alias", self._active.address_alias),
            address=kwargs.get("address", self._active.address),
        )
        return self._active

    def _next_addr(self) -> str:
        byte = format(self._next_idx % 256, "02x")
        self._next_idx += 1
        return "0x" + byte * 32

    # --- reads ---

    async def active_state(self) -> ActiveState:
        await asyncio.sleep(0.05)
        return self._active

    async def list_groups(self) -> list[GroupInfo]:
        await asyncio.sleep(0.05)
        return list(self._groups)

    async def list_profiles(self, group_name: str) -> list[ProfileInfo]:
        await asyncio.sleep(0.05)
        return list(self._profiles.get(group_name, []))

    async def list_addresses(self, group_name: str) -> list[AddressInfo]:
        await asyncio.sleep(0.05)
        return list(self._addresses.get(group_name, []))

    # --- group mutations ---

    async def create_group(
        self, name: str, protocol: GroupProtocol,
        profiles: list[dict], keys: list[dict],
    ) -> GroupInfo:
        await asyncio.sleep(0.05)
        plist = [
            ProfileInfo(name=p["name"], group_name=name, url=p["url"], is_active=(i == 0))
            for i, p in enumerate(profiles)
        ]
        alist = [
            AddressInfo(
                alias=k["alias"], address=self._next_addr(),
                group_name=name, key_scheme="ed25519", is_active=(i == 0),
            )
            for i, k in enumerate(keys)
        ]
        self._profiles[name] = plist
        self._addresses[name] = alist
        g = GroupInfo(name=name, protocol=protocol,
                      profile_count=len(plist), address_count=len(alist),
                      is_active=False)
        self._groups.append(g)
        return g

    async def delete_group(self, name: str) -> str:
        await asyncio.sleep(0.05)
        was_active = any(g.name == name and g.is_active for g in self._groups)
        self._groups = [g for g in self._groups if g.name != name]
        self._profiles.pop(name, None)
        self._addresses.pop(name, None)
        if was_active and self._groups:
            g0 = self._groups[0]
            self._groups[0] = replace(g0, is_active=True)
            p0 = self._profiles.get(g0.name, [])
            if p0:
                self._profiles[g0.name] = (
                    [replace(p0[0], is_active=True)] + [replace(p, is_active=False) for p in p0[1:]]
                )
            a0 = self._addresses.get(g0.name, [])
            if a0:
                self._addresses[g0.name] = (
                    [replace(a0[0], is_active=True)] + [replace(a, is_active=False) for a in a0[1:]]
                )
            active_p = self._profiles.get(g0.name, [None])[0]
            active_a = self._addresses.get(g0.name, [None])[0]
            self._active = ActiveState(
                config_path=self._active.config_path,
                group_name=g0.name,
                profile_name=active_p.name if active_p else None,
                profile_url=active_p.url if active_p else None,
                address_alias=active_a.alias if active_a else None,
                address=active_a.address if active_a else None,
            )
            return g0.name
        return self._active.group_name or (self._groups[0].name if self._groups else "")

    async def set_active_group(self, name: str) -> ActiveState:
        await asyncio.sleep(0.05)
        self._groups = [replace(g, is_active=(g.name == name)) for g in self._groups]
        p_list = self._profiles.get(name, [])
        a_list = self._addresses.get(name, [])
        active_p = next((p for p in p_list if p.is_active), p_list[0] if p_list else None)
        active_a = next((a for a in a_list if a.is_active), a_list[0] if a_list else None)
        return self._update_active(
            group_name=name,
            profile_name=active_p.name if active_p else None,
            profile_url=active_p.url if active_p else None,
            address_alias=active_a.alias if active_a else None,
            address=active_a.address if active_a else None,
        )

    # --- profile mutations ---

    async def create_profile(self, group_name: str, name: str, url: str) -> ProfileInfo:
        await asyncio.sleep(0.05)
        plist = self._profiles.setdefault(group_name, [])
        p = ProfileInfo(name=name, group_name=group_name, url=url, is_active=not plist)
        plist.append(p)
        g = self._find_group(group_name)
        if g:
            self._replace_group(replace(g, profile_count=len(plist)))
        return p

    async def update_profile(self, group_name: str, name: str, url: str) -> ProfileInfo:
        await asyncio.sleep(0.05)
        plist = self._profiles.get(group_name, [])
        for i, p in enumerate(plist):
            if p.name == name:
                updated = replace(p, url=url)
                plist[i] = updated
                return updated
        raise ValueError(f"Profile {name!r} not found in group {group_name!r}")

    async def delete_profile(self, group_name: str, name: str) -> None:
        await asyncio.sleep(0.05)
        plist = self._profiles.get(group_name, [])
        was_active = any(p.name == name and p.is_active for p in plist)
        self._profiles[group_name] = [p for p in plist if p.name != name]
        remaining = self._profiles[group_name]
        if was_active and remaining:
            self._profiles[group_name] = (
                [replace(remaining[0], is_active=True)] + [replace(p, is_active=False) for p in remaining[1:]]
            )
            if self._active.group_name == group_name:
                self._update_active(profile_name=remaining[0].name)
        g = self._find_group(group_name)
        if g:
            self._replace_group(replace(g, profile_count=len(remaining)))

    async def set_active_profile(self, group_name: str, name: str) -> ActiveState:
        await asyncio.sleep(0.05)
        plist = self._profiles.get(group_name, [])
        self._profiles[group_name] = [replace(p, is_active=(p.name == name)) for p in plist]
        active_p = next((p for p in plist if p.name == name), None)
        return self._update_active(
            profile_name=name,
            profile_url=active_p.url if active_p else None,
        )

    # --- address mutations ---

    async def generate_keypair(self, group_name: str, alias: str) -> tuple[AddressInfo, str]:
        await asyncio.sleep(0.05)
        alist = self._addresses.setdefault(group_name, [])
        addr = self._next_addr()
        a = AddressInfo(alias=alias, address=addr, group_name=group_name,
                        key_scheme="ed25519", is_active=not alist)
        alist.append(a)
        g = self._find_group(group_name)
        if g:
            self._replace_group(replace(g, address_count=len(alist)))
        return a, _FAKE_MNEMONIC

    async def import_address(self, group_name: str, alias: str, private_key: str) -> AddressInfo:
        await asyncio.sleep(0.05)
        alist = self._addresses.setdefault(group_name, [])
        addr = self._next_addr()
        a = AddressInfo(alias=alias, address=addr, group_name=group_name,
                        key_scheme="ed25519", is_active=not alist)
        alist.append(a)
        g = self._find_group(group_name)
        if g:
            self._replace_group(replace(g, address_count=len(alist)))
        return a

    async def rename_alias(self, group_name: str, existing_alias: str, new_alias: str) -> AddressInfo:
        await asyncio.sleep(0.05)
        alist = self._addresses.get(group_name, [])
        for i, a in enumerate(alist):
            if a.alias == existing_alias:
                updated = replace(a, alias=new_alias)
                alist[i] = updated
                if self._active.group_name == group_name and self._active.address_alias == existing_alias:
                    self._update_active(address_alias=new_alias)
                return updated
        raise ValueError(f"Alias {existing_alias!r} not found in group {group_name!r}")

    async def delete_address(self, group_name: str, alias: str) -> None:
        await asyncio.sleep(0.05)
        alist = self._addresses.get(group_name, [])
        was_active = any(a.alias == alias and a.is_active for a in alist)
        self._addresses[group_name] = [a for a in alist if a.alias != alias]
        remaining = self._addresses[group_name]
        if was_active and remaining:
            self._addresses[group_name] = (
                [replace(remaining[0], is_active=True)] + [replace(a, is_active=False) for a in remaining[1:]]
            )
            if self._active.group_name == group_name:
                self._update_active(address_alias=remaining[0].alias, address=remaining[0].address)
        g = self._find_group(group_name)
        if g:
            self._replace_group(replace(g, address_count=len(remaining)))

    async def set_active_address(self, group_name: str, alias: str) -> ActiveState:
        await asyncio.sleep(0.05)
        alist = self._addresses.get(group_name, [])
        self._addresses[group_name] = [replace(a, is_active=(a.alias == alias)) for a in alist]
        addr = next((a.address for a in alist if a.alias == alias), None)
        return self._update_active(address_alias=alias, address=addr)

    async def get_chain_info(self) -> ChainInfo:
        return ChainInfo(chain_id="faux-chain", epoch="0", reference_gas_price="750", validator_count="0")

    async def execute_read(self, command_name: str, kwargs: dict, cursor: bytes | None) -> ReadResult:
        await asyncio.sleep(0.05)
        return ReadResult(
            json_str=f'{{"stub": "faux result for {command_name}", "kwargs": {list(kwargs.keys())}}}',
            cursor=None,
            error=None,
        )

    async def aclose(self) -> None:
        pass

    async def get_owned_objects(self, owner: str) -> list[ObjectSummaryInfo]:
        await asyncio.sleep(0.05)
        return [
            ObjectSummaryInfo(object_id="0x" + "aa" * 32, object_type="0x2::coin::Coin<0x2::sui::SUI>"),
            ObjectSummaryInfo(object_id="0x" + "bb" * 32, object_type="0x2::coin::Coin<0x2::sui::SUI>"),
            ObjectSummaryInfo(object_id="0x" + "cc" * 32, object_type="0xdeadbeef::nft::MyNFT"),
        ]

    async def get_owned_coins(self, owner: str) -> list[ObjectSummaryInfo]:
        await asyncio.sleep(0.05)
        return [
            ObjectSummaryInfo(object_id="0x" + "aa" * 32, object_type="0x2::coin::Coin<0x2::sui::SUI>"),
            ObjectSummaryInfo(object_id="0x" + "bb" * 32, object_type="0x2::coin::Coin<0x2::sui::SUI>"),
        ]

    async def get_gas_objects(self, owner: str) -> list[GasObjectInfo]:
        await asyncio.sleep(0.05)
        return [
            GasObjectInfo(object_id="0x" + "aa" * 32, balance="1000000000"),
            GasObjectInfo(object_id="0x" + "bb" * 32, balance="2500000000"),
        ]

    async def get_coin_balances(self, owner: str) -> str:
        await asyncio.sleep(0.05)
        return '{"balances": [{"coin_type": "0x2::sui::SUI", "total_balance": "3500000000"}]}'
