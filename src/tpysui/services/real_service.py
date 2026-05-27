#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

from pysui import PysuiConfiguration
from pysui.abstracts.client_keypair import SignatureScheme
from pysui.sui.sui_common.config import confgroup as _cg
from pysui.sui.sui_common.factory import client_factory
from pysui.sui.sui_common import sui_commands as _sc

from .base import (
    ActiveState, AddressInfo, ChainInfo, GasObjectInfo, GroupInfo, GroupProtocol,
    ObjectSummaryInfo, ProfileInfo, ReadResult, SuiService,
)

_COMMAND_MAP: dict[str, type] = {
    "GetCoinMetaData": _sc.GetCoinMetaData,
    "GetAddressCoinBalance": _sc.GetAddressCoinBalance,
    "GetAddressCoinBalances": _sc.GetAddressCoinBalances,
    "GetCoins": _sc.GetCoins,
    "GetGas": _sc.GetGas,
    "GetCoinSummary": _sc.GetCoinSummary,
    "GetStaked": _sc.GetStaked,
    "GetDelegatedStakes": _sc.GetDelegatedStakes,
    "GetObject": _sc.GetObject,
    "GetPastObject": _sc.GetPastObject,
    "GetObjectSummary": _sc.GetObjectSummary,
    "GetObjectContent": _sc.GetObjectContent,
    "GetObjectsOwnedByAddress": _sc.GetObjectsOwnedByAddress,
    "GetObjectsForType": _sc.GetObjectsForType,
    "GetMultipleObjects": _sc.GetMultipleObjects,
    "GetMultipleObjectSummary": _sc.GetMultipleObjectSummary,
    "GetMultipleObjectContent": _sc.GetMultipleObjectContent,
    "GetMultiplePastObjects": _sc.GetMultiplePastObjects,
    "GetDynamicFields": _sc.GetDynamicFields,
    "GetBasicCurrentEpochInfo": _sc.GetBasicCurrentEpochInfo,
    "GetEpoch": _sc.GetEpoch,
    "GetLatestCheckpoint": _sc.GetLatestCheckpoint,
    "GetCheckpointBySequence": _sc.GetCheckpointBySequence,
    "GetCheckpointByDigest": _sc.GetCheckpointByDigest,
    "GetChainIdentifier": _sc.GetChainIdentifier,
    "GetLatestSuiSystemState": _sc.GetLatestSuiSystemState,
    "GetProtocolConfig": _sc.GetProtocolConfig,
    "GetCurrentValidators": _sc.GetCurrentValidators,
    "GetPackage": _sc.GetPackage,
    "GetPackageVersions": _sc.GetPackageVersions,
    "GetModule": _sc.GetModule,
    "GetMoveDataType": _sc.GetMoveDataType,
    "GetStructure": _sc.GetStructure,
    "GetStructures": _sc.GetStructures,
    "GetFunction": _sc.GetFunction,
    "GetFunctions": _sc.GetFunctions,
    "GetNameServiceAddress": _sc.GetNameServiceAddress,
    "GetNameServiceNames": _sc.GetNameServiceNames,
    "GetTransaction": _sc.GetTransaction,
    "GetTransactions": _sc.GetTransactions,
    "GetTransactionKind": _sc.GetTransactionKind,
}


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
        self._read_client = None
        self._client_group: str | None = None
        self._client_profile: str | None = None

    async def active_state(self) -> ActiveState:
        try:
            group = self._cfg.active_group
            profile = group.using_profile
            profile_url = next(
                (p.url for p in group.profiles if p.profile_name == profile), None
            )
            address = group.using_address if group.address_list else None
            alias = group.active_alias if group.address_list else None
        except Exception:
            profile = profile_url = address = alias = None
        return ActiveState(
            config_path=self._cfg.config,
            group_name=self._cfg.active_group_name,
            profile_name=profile,
            profile_url=profile_url,
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

    async def _get_read_client(self):
        try:
            active_group = self._cfg.active_group_name
            active_profile = self._cfg.active_profile
        except Exception:
            active_group = active_profile = None
        if (
            self._read_client is None
            or self._client_group != active_group
            or self._client_profile != active_profile
        ):
            if self._read_client is not None:
                try:
                    await self._read_client.close()
                except Exception:
                    pass
            self._read_client = client_factory(self._cfg)
            self._client_group = active_group
            self._client_profile = active_profile
        return self._read_client

    async def aclose(self) -> None:
        if self._read_client is not None:
            try:
                await self._read_client.close()
            except Exception:
                pass
            self._read_client = None

    async def get_chain_info(self) -> ChainInfo:
        client = await self._get_read_client()
        chain_id = epoch_str = ref_gas = validator_count = "—"
        try:
            res = await client.execute(command=_sc.GetChainIdentifier())
            if res.is_ok() and isinstance(res.result_data, str):
                chain_id = res.result_data
        except Exception:
            pass
        try:
            res = await client.execute(command=_sc.GetEpoch())
            if res.is_ok():
                ep = res.result_data.epoch
                if ep is not None:
                    epoch_str = str(ep.epoch) if ep.epoch is not None else "—"
                    ref_gas = str(ep.reference_gas_price) if ep.reference_gas_price is not None else "—"
                    vs = ep.system_state.validators if ep.system_state else None
                    validator_count = str(len(vs.active_validators)) if vs else "—"
        except Exception:
            pass
        return ChainInfo(
            chain_id=chain_id,
            epoch=epoch_str,
            reference_gas_price=ref_gas,
            validator_count=validator_count,
        )

    async def execute_read(self, command_name: str, kwargs: dict, cursor: bytes | None) -> ReadResult:
        command_class = _COMMAND_MAP.get(command_name)
        if command_class is None:
            return ReadResult(json_str=None, cursor=None, error=f"Unknown command: {command_name}")
        is_pageable = getattr(command_class, "is_pageable_grpc", False) or getattr(command_class, "is_pageable_gql", False)
        try:
            call_kwargs = dict(kwargs)
            if cursor is not None and is_pageable:
                call_kwargs["next_page_token"] = cursor
            command = command_class(**call_kwargs)
            client = await self._get_read_client()
            result = await client.execute(command=command)
            if result.is_ok():
                next_cursor = getattr(result.result_data, "next_page_token", None) if is_pageable else None
                data = result.result_data
                if isinstance(data, str):
                    json_str = data
                else:
                    json_str = data.to_json(indent=2)
                return ReadResult(
                    json_str=json_str,
                    cursor=next_cursor or None,
                    error=None,
                )
            return ReadResult(json_str=None, cursor=None, error=result.result_string or "Unknown error")
        except Exception as exc:
            return ReadResult(json_str=None, cursor=None, error=str(exc) or f"{type(exc).__name__} (no message)")

    async def get_owned_objects(self, owner: str) -> list[ObjectSummaryInfo]:
        try:
            client = await self._get_read_client()
            result = await client.execute_for_all(command=_sc.GetObjectsOwnedByAddress(owner=owner))
            if not result.is_ok():
                return []
            objects = []
            for obj in result.result_data.objects:
                obj_id = str(obj.object_id or "")
                if obj_id:
                    objects.append(ObjectSummaryInfo(
                        object_id=obj_id,
                        object_type=str(obj.object_type or ""),
                        digest=str(obj.digest or ""),
                        version=str(obj.version or 0),
                    ))
            return objects
        except Exception:
            return []

    async def get_owned_coins(self, owner: str) -> list[ObjectSummaryInfo]:
        try:
            client = await self._get_read_client()
            result = await client.execute_for_all(command=_sc.GetCoins(owner=owner))
            if not result.is_ok():
                return []
            objects = []
            for obj in result.result_data.objects:
                obj_id = str(obj.object_id or "")
                obj_type = str(obj.object_type or "")
                if obj_id:
                    objects.append(ObjectSummaryInfo(object_id=obj_id, object_type=obj_type))
            return objects
        except Exception:
            return []

    async def get_gas_objects(self, owner: str) -> list[GasObjectInfo]:
        try:
            client = await self._get_read_client()
            result = await client.execute_for_all(command=_sc.GetGas(owner=owner))
            if not result.is_ok():
                return []
            objects = []
            for obj in result.result_data.objects:
                obj_id = str(obj.object_id or "")
                if obj_id:
                    objects.append(GasObjectInfo(
                        object_id=obj_id,
                        balance=str(obj.balance or 0),
                        digest=str(obj.digest or ""),
                        version=str(obj.version or 0),
                    ))
            return objects
        except Exception:
            return []

    async def get_coin_balances(self, owner: str) -> str:
        try:
            client = await self._get_read_client()
            result = await client.execute_for_all(command=_sc.GetAddressCoinBalances(owner=owner))
            if not result.is_ok():
                return ""
            return result.result_data.to_json(indent=2)
        except Exception:
            return ""
