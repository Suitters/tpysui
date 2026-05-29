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

    async def run_utility(self, name: str, args: dict, simulate: bool) -> "UtilityResultDTO":
        from .base import UtilityResultDTO
        _handlers = {
            "transfer-object": self._run_transfer_object,
            "transfer-sui": self._run_transfer_sui,
            "pay-sui": self._run_pay_sui,
            "merge-coin": self._run_merge_coin,
            "split-coin": self._run_split_coin,
            "split-coin-equally": self._run_split_coin_equally,
            "smash-coins": self._run_smash_coins,
            "splay-coins": self._run_splay_coins,
            "coin-to-account": self._run_coin_to_account,
            "account-to-coin": self._run_account_to_coin,
            "move-struct-to-bcs": self._run_move_struct_to_bcs,
        }
        handler = _handlers.get(name)
        if handler is None:
            return UtilityResultDTO(
                simulated=simulate, success=False,
                error=f"'{name}' not yet implemented",
                digest=None, gas_used=None,
                mutated=[], created=[], deleted=[], events=[], raw_json="",
            )
        try:
            return await handler(args, simulate)
        except Exception as exc:
            return UtilityResultDTO(
                simulated=simulate, success=False,
                error=str(exc) or f"{type(exc).__name__} (no message)",
                digest=None, gas_used=None,
                mutated=[], created=[], deleted=[], events=[], raw_json="",
            )

    async def _exec_or_sim(self, txer, client, args: dict, simulate: bool) -> "UtilityResultDTO":
        from pysui.sui.sui_common import sui_commands as _sc
        gas_mode = args.get("gas_mode", "Use Gas Coin")
        budget = args.get("budget")
        gas_list = args.get("gas") or None
        owner = args.get("owner", "")
        if simulate:
            tx_kind = txer.raw_kind()
            sim_cmd = _sc.SimulateTransactionKind(
                tx_kind, {"sender": owner}, checks_enabled=True,
            )
            result = await client.execute(command=sim_cmd)
        else:
            build_result = await txer.build_and_sign(
                gas_budget=int(budget) if budget else None,
                use_gas_objects=gas_list if gas_list else None,
                use_account_for_gas=(gas_mode == "Use Account Balance"),
                auto_gas=(gas_mode == "Auto Select"),
            )
            tx_bytes = build_result["tx_bytestr"]
            sigs = build_result["sig_array"]
            exec_cmd = _sc.ExecuteTransaction(tx_bytestr=tx_bytes, sig_array=sigs)
            result = await client.execute(command=exec_cmd)
        return self._parse_utility_result(result, simulate)

    def _parse_utility_result(self, result, simulate: bool) -> "UtilityResultDTO":
        from .base import UtilityResultDTO
        if not result.is_ok():
            return UtilityResultDTO(
                simulated=simulate, success=False,
                error=result.result_string or "Execution failed",
                digest=None, gas_used=None,
                mutated=[], created=[], deleted=[], events=[], raw_json="",
            )
        data = result.result_data  # ExecutedTransaction proto dataclass
        raw_json = data.to_json(indent=2) if hasattr(data, "to_json") else str(data)
        digest = (data.digest or None) if not simulate else None
        effects = data.effects  # TransactionEffects | None
        gas_used = None
        if effects and effects.gas_used:
            try:
                computation = int(getattr(effects.gas_used, "computation_cost", 0) or 0)
                storage = int(getattr(effects.gas_used, "storage_cost", 0) or 0)
                gas_used = computation + storage
            except Exception:
                pass
        mutated: list[str] = []
        created: list[str] = []
        deleted: list[str] = []
        if effects:
            for obj in (effects.changed_objects or []):
                oid = obj.object_id
                if not oid:
                    continue
                op = obj.id_operation
                if op == 1:    # ChangedObjectIdOperation.NONE — object mutated
                    mutated.append(str(oid))
                elif op == 2:  # ChangedObjectIdOperation.CREATED
                    created.append(str(oid))
                elif op == 3:  # ChangedObjectIdOperation.DELETED
                    deleted.append(str(oid))
        events: list[str] = []
        try:
            ev_container = data.events
            if ev_container:
                for ev in (getattr(ev_container, "events", None) or []):
                    events.append(ev.to_json() if hasattr(ev, "to_json") else str(ev))
        except Exception:
            pass
        return UtilityResultDTO(
            simulated=simulate, success=True, error=None,
            digest=str(digest) if digest else None,
            gas_used=gas_used,
            mutated=mutated, created=created, deleted=deleted,
            events=events, raw_json=raw_json,
        )

    async def _run_transfer_object(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        owner = args["owner"]
        transfers = args.get("transfer", [])
        recipient = args["recipient"]
        client = await self._get_read_client()
        txer = await client.transaction(initial_sender=owner)
        await txer.transfer_objects(transfers=transfers, recipient=recipient)
        return await self._exec_or_sim(txer, client, args, simulate)

    async def _run_transfer_sui(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        owner = args["owner"]
        takes = args.get("takes_from", "Tx Gas")
        mists = int(args["mists"])
        recipient = args["recipient"]
        client = await self._get_read_client()
        txer = await client.transaction(initial_sender=owner)
        coin = txer.gas if takes == "Tx Gas" else takes
        res = await txer.split_coin(coin=coin, amounts=[mists])
        await txer.transfer_objects(transfers=[res], recipient=recipient)
        return await self._exec_or_sim(txer, client, args, simulate)

    async def _run_pay_sui(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        owner = args["owner"]
        payments = args.get("payments", [])
        client = await self._get_read_client()
        txer = await client.transaction(initial_sender=owner)
        for payment in payments:
            coin_from = payment.get("coin_from", "Tx Gas")
            mists = int(payment["mists"])
            recip = payment["recipient"]
            coin = txer.gas if coin_from == "Tx Gas" else coin_from
            res = await txer.split_coin(coin=coin, amounts=[mists])
            await txer.transfer_objects(transfers=[res], recipient=recip)
        return await self._exec_or_sim(txer, client, args, simulate)

    async def _run_merge_coin(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        owner = args["owner"]
        merge_to = args.get("merge_to", "Tx Gas")
        coins_to_merge = args.get("coins_to_merge", [])
        client = await self._get_read_client()
        txer = await client.transaction(initial_sender=owner)
        primary = txer.gas if merge_to == "Tx Gas" else merge_to
        await txer.merge_coins(merge_to=primary, merge_from=coins_to_merge)
        return await self._exec_or_sim(txer, client, args, simulate)

    async def _run_split_coin(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        owner = args["owner"]
        splits_from = args.get("splits_from", "Tx Gas")
        mists = args.get("mists", [])
        client = await self._get_read_client()
        txer = await client.transaction(initial_sender=owner)
        coin = txer.gas if splits_from == "Tx Gas" else splits_from
        amounts = [int(m) for m in (mists if isinstance(mists, list) else [mists])]
        split_res = await txer.split_coin(coin=coin, amounts=amounts)
        transfers = split_res if len(amounts) > 1 else [split_res]
        await txer.transfer_objects(transfers=transfers, recipient=owner)
        return await self._exec_or_sim(txer, client, args, simulate)

    async def _run_split_coin_equally(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        owner = args["owner"]
        splits_from = args.get("splits_from", "Tx Gas")
        split_count = int(args["split_count"])
        client = await self._get_read_client()
        txer = await client.transaction(initial_sender=owner)
        coin = txer.gas if splits_from == "Tx Gas" else splits_from
        await txer.split_coin_equal(coin=coin, split_count=split_count)
        return await self._exec_or_sim(txer, client, args, simulate)

    async def _run_smash_coins(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        from pysui.sui.sui_common import async_funcs as asfn
        from .base import UtilityResultDTO
        owner = args["owner"]
        exclude = args.get("exclude") or []
        client = await self._get_read_client()
        op_status, effects, gas_coin_id, exec_result = await asfn.merge_sui(
            client=client, address=owner, merge_only=None, exclude=exclude, wait=False,
        )
        success = str(op_status).lower() not in ("failed", "error", "ops_fail")
        if effects is not None:
            raw_json = effects.to_json(indent=2) if hasattr(effects, "to_json") else str(effects)
        else:
            raw_json = ""
        return UtilityResultDTO(
            simulated=False, success=success,
            error=None if success else str(op_status),
            digest=None, gas_used=None,
            mutated=[], created=[], deleted=[], events=[], raw_json=raw_json,
        )

    async def _run_splay_coins(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        from pysui.sui.sui_common import async_funcs as asfn
        from .base import UtilityResultDTO
        owner = args["owner"]
        exclude = args.get("exclude") or []
        mist = args.get("mist")
        number = args.get("number")
        recipients = args.get("recipients") or []
        if number and recipients:
            return UtilityResultDTO(
                simulated=False, success=False,
                error="number and recipients are mutually exclusive",
                digest=None, gas_used=None,
                mutated=[], created=[], deleted=[], events=[], raw_json="",
            )
        if not number and not recipients:
            return UtilityResultDTO(
                simulated=False, success=False,
                error="Must provide either number or recipients",
                digest=None, gas_used=None,
                mutated=[], created=[], deleted=[], events=[], raw_json="",
            )
        if number and int(number) < 2:
            return UtilityResultDTO(
                simulated=False, success=False,
                error="number must be >= 2",
                digest=None, gas_used=None,
                mutated=[], created=[], deleted=[], events=[], raw_json="",
            )
        client = await self._get_read_client()
        op_status, effects, gas_coin_id, exec_result = await asfn.merge_sui(
            client=client, address=owner, merge_only=None, exclude=exclude, wait=False,
        )
        success = str(op_status).lower() not in ("failed", "error", "ops_fail")
        if not success:
            return UtilityResultDTO(
                simulated=False, success=False, error=str(op_status),
                digest=None, gas_used=None,
                mutated=[], created=[], deleted=[], events=[], raw_json="",
            )
        gas_bal = 0
        if not mist:
            gas_result = await client.execute_for_all(command=_sc.GetGas(owner=owner))
            if gas_result.is_ok():
                coins = list(getattr(gas_result.result_data, "objects", None) or [])
                for c in coins:
                    if c.object_id == gas_coin_id:
                        gas_bal = int(c.balance or 0)
                        break
        txer = await client.transaction(initial_sender=owner)
        if number:
            count = int(number)
            gas_reserve = count * 1_988_000
            distro = int(mist) if mist else int((gas_bal - gas_reserve) / count)
            amounts = [distro] * count
            r_coins = await txer.split_coin(coin=txer.gas, amounts=amounts)
            await txer.transfer_objects(transfers=r_coins, recipient=owner)
        else:
            r_count = len(recipients)
            gas_reserve = r_count * 1_988_000
            distro = int(mist) if mist else int((gas_bal - gas_reserve) / r_count)
            if r_count == 1:
                r_coin = await txer.split_coin(coin=txer.gas, amounts=[distro])
                await txer.transfer_objects(transfers=[r_coin], recipient=recipients[0])
            else:
                amounts = [distro] * r_count
                r_coins = await txer.split_coin(coin=txer.gas, amounts=amounts)
                for idx, recip in enumerate(recipients):
                    await txer.transfer_objects(transfers=[r_coins[idx]], recipient=recip)
        return await self._exec_or_sim(txer, client, args, simulate=simulate)

    async def _run_coin_to_account(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        owner = args["owner"]
        coin_from = args.get("coin_from", "Tx Gas")
        amount = int(args["amount"])
        recipient = args.get("recipient", owner)
        client = await self._get_read_client()
        txer = await client.transaction(initial_sender=owner)
        coin = txer.gas if coin_from == "Tx Gas" else coin_from
        split_res = await txer.split_coin(coin=coin, amounts=[amount])
        await txer.fund_address_accumulator(funds=split_res, recipient=recipient)
        return await self._exec_or_sim(txer, client, args, simulate)

    async def _run_account_to_coin(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        from pysui.sui.sui_common.trxn_base import FundsSource
        owner = args["owner"]
        amount = args.get("amount")
        client = await self._get_read_client()
        txer = await client.transaction(initial_sender=owner)
        amt = int(amount) if amount else None
        result = await txer.coin_from_address_accumulator(source=FundsSource.SENDER, amount=amt)
        await txer.transfer_objects(transfers=[result], recipient=owner)
        return await self._exec_or_sim(txer, client, args, simulate)

    async def _run_move_struct_to_bcs(self, args: dict, simulate: bool) -> "UtilityResultDTO":
        import json as _json
        from pathlib import Path
        from pysui.sui.sui_common.move_to_bcs import MoveDataType
        import pysui.sui.sui_common.mtobcs_types as mtypes
        from .base import UtilityResultDTO
        directive_file = args.get("directive_file", "")
        if not directive_file or not Path(directive_file).exists():
            return UtilityResultDTO(
                simulated=False, success=False,
                error="Directive file not found or not set",
                digest=None, gas_used=None,
                mutated=[], created=[], deleted=[], events=[], raw_json="",
            )
        json_data = _json.loads(Path(directive_file).read_text(encoding="utf-8"))
        package_targets = mtypes.Targets.load_declarations(json_data)
        client = await self._get_read_client()
        generated = []
        for package in package_targets.targets:
            mst = MoveDataType(client=client, target=package)
            await mst.parse_move_target()
            await mst.compile_bcs()
            bcs_py = await mst.emit_bcs_source()
            out_path = Path(package.out_file)
            out_path.write_text(bcs_py, encoding="utf-8")
            generated.append(str(out_path))
        return UtilityResultDTO(
            simulated=False, success=True, error=None,
            digest=None, gas_used=None,
            mutated=[], created=generated, deleted=[], events=[],
            raw_json=_json.dumps({"generated": generated}, indent=2),
        )
