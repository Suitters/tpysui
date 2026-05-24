from pysui import PysuiConfiguration
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_common.config import confgroup as _cg

from .base import (
    ActiveState, AddressInfo, GroupInfo, GroupProtocol, ProfileInfo, SuiService,
)


def _to_our(p: _cg.GroupProtocol) -> GroupProtocol:
    if p == _cg.GroupProtocol.GRAPHQL:
        return GroupProtocol.GRAPHQL
    if p == _cg.GroupProtocol.GRPC:
        return GroupProtocol.GRPC
    return GroupProtocol.OTHER


def _to_pysui(p: GroupProtocol) -> _cg.GroupProtocol:
    if p == GroupProtocol.GRAPHQL:
        return _cg.GroupProtocol.GRAPHQL
    if p == GroupProtocol.GRPC:
        return _cg.GroupProtocol.GRPC
    return _cg.GroupProtocol.OTHER


def _scheme_name(cfg: PysuiConfiguration, address: str, group_name: str) -> str:
    try:
        kp = cfg.keypair_for_address(address=address, in_group=group_name)
        return kp.scheme.name
    except Exception:
        return "Unknown"


class RealSuiService(SuiService):
    def __init__(self, config: PysuiConfiguration) -> None:
        self._cfg = config

    async def active_state(self) -> ActiveState:
        try:
            group = self._cfg.active_group
            profile = group.using_profile
            address = group.using_address if group.address_list else None
            alias = group.active_alias if group.address_list else None
        except Exception:
            profile = address = alias = None
        return ActiveState(
            config_path=self._cfg.config,
            group_name=self._cfg.active_group_name,
            profile_name=profile,
            address_alias=alias,
            address=address,
        )

    async def list_groups(self) -> list[GroupInfo]:
        active = self._cfg.active_group_name
        return [
            GroupInfo(
                name=g.group_name,
                protocol=_to_our(g.group_protocol),
                profile_count=len(g.profiles),
                address_count=len(g.address_list),
                is_active=(g.group_name == active),
            )
            for g in self._cfg.model.groups
        ]

    async def list_profiles(self, group_name: str) -> list[ProfileInfo]:
        group = self._cfg.model.get_group(group_name=group_name)
        return [
            ProfileInfo(
                name=p.profile_name,
                group_name=group_name,
                url=p.url,
                is_active=(p.profile_name == group.using_profile),
            )
            for p in group.profiles
        ]

    async def list_addresses(self, group_name: str) -> list[AddressInfo]:
        group = self._cfg.model.get_group(group_name=group_name)
        return [
            AddressInfo(
                alias=alias_obj.alias,
                address=addr,
                group_name=group_name,
                key_scheme=_scheme_name(self._cfg, addr, group_name),
                is_active=(addr == group.using_address),
            )
            for addr, alias_obj in zip(group.address_list, group.alias_list)
        ]

    async def create_group(
        self, name: str, protocol: GroupProtocol,
        profiles: list[dict], keys: list[dict],
    ) -> GroupInfo:
        pysui_proto = _to_pysui(protocol)
        if keys:
            profile_block = [
                {
                    "profile_name": p["name"], "url": p["url"],
                    "faucet_url": None, "faucet_status_url": None,
                    "make_active": (i == 0),
                }
                for i, p in enumerate(profiles)
            ]
            key_block = [{"key_string": k["public_key"], "alias": k["alias"]} for k in keys]
            self._cfg.new_group(
                group_name=name,
                profile_block=profile_block,
                key_block=key_block,
                active_address_index=0,
                group_protocol=pysui_proto,
                persist=True,
            )
        else:
            self._cfg.model.add_group(
                group=_cg.ProfileGroup(name, "", "", [], [], [], [], pysui_proto),
                make_active=False,
            )
            for p in profiles:
                self._cfg.new_profile(
                    profile_name=p["name"], url=p["url"],
                    in_group=name, persist=False,
                )
            self._cfg.save()
        group = self._cfg.model.get_group(group_name=name)
        return GroupInfo(
            name=group.group_name,
            protocol=_to_our(group.group_protocol),
            profile_count=len(group.profiles),
            address_count=len(group.address_list),
            is_active=(group.group_name == self._cfg.active_group_name),
        )

    async def delete_group(self, name: str) -> str:
        new_active = self._cfg.model.remove_group(group_name=name)
        self._cfg.save()
        return new_active

    async def set_active_group(self, name: str) -> ActiveState:
        self._cfg.make_active(group_name=name, persist=True)
        return await self.active_state()

    async def create_profile(self, group_name: str, name: str, url: str) -> ProfileInfo:
        self._cfg.new_profile(profile_name=name, url=url, in_group=group_name, persist=True)
        group = self._cfg.model.get_group(group_name=group_name)
        return ProfileInfo(
            name=name, group_name=group_name, url=url,
            is_active=(name == group.using_profile),
        )

    async def update_profile(self, group_name: str, name: str, url: str) -> ProfileInfo:
        self._cfg.update_profile(profile_name=name, url=url, in_group=group_name, persist=True)
        group = self._cfg.model.get_group(group_name=group_name)
        return ProfileInfo(
            name=name, group_name=group_name, url=url,
            is_active=(name == group.using_profile),
        )

    async def delete_profile(self, group_name: str, name: str) -> None:
        self._cfg.model.get_group(group_name=group_name).remove_profile(profile_name=name)
        self._cfg.save()

    async def set_active_profile(self, group_name: str, name: str) -> ActiveState:
        self._cfg.make_active(group_name=group_name, profile_name=name, persist=True)
        return await self.active_state()

    async def generate_keypair(self, group_name: str, alias: str) -> tuple[AddressInfo, str]:
        mnemonic, address = self._cfg.new_keypair(
            of_keytype=SignatureScheme.ED25519,
            in_group=group_name,
            alias=alias,
            word_counts=12,
            persist=True,
        )
        group = self._cfg.model.get_group(group_name=group_name)
        return AddressInfo(
            alias=alias,
            address=address,
            group_name=group_name,
            key_scheme=_scheme_name(self._cfg, address, group_name),
            is_active=(address == group.using_address),
        ), mnemonic

    async def import_address(self, group_name: str, alias: str, private_key: str) -> AddressInfo:
        addresses = self._cfg.add_keys(
            key_block=[{"key_string": private_key, "alias": alias}],
            in_group=group_name,
            persist=True,
        )
        address = addresses[0]
        group = self._cfg.model.get_group(group_name=group_name)
        return AddressInfo(
            alias=alias,
            address=address,
            group_name=group_name,
            key_scheme=_scheme_name(self._cfg, address, group_name),
            is_active=(address == group.using_address),
        )

    async def rename_alias(
        self, group_name: str, existing_alias: str, new_alias: str,
    ) -> AddressInfo:
        address = self._cfg.rename_alias(
            existing_alias=existing_alias,
            new_alias=new_alias,
            in_group=group_name,
            persist=True,
        )
        group = self._cfg.model.get_group(group_name=group_name)
        return AddressInfo(
            alias=new_alias,
            address=address,
            group_name=group_name,
            key_scheme=_scheme_name(self._cfg, address, group_name),
            is_active=(address == group.using_address),
        )

    async def delete_address(self, group_name: str, alias: str) -> None:
        self._cfg.model.get_group(group_name=group_name).remove_alias(alias_name=alias)
        self._cfg.save()

    async def set_active_address(self, group_name: str, alias: str) -> ActiveState:
        self._cfg.make_active(group_name=group_name, alias=alias, persist=True)
        return await self.active_state()
