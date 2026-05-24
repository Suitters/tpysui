from .base import ArgInfo, CommandInfo

_a = ArgInfo  # shorthand

COMMAND_REGISTRY: list[CommandInfo] = [
    # Coin / Balance
    CommandInfo("GetCoinMetaData", "Coin / Balance",
        (_a("coin_type", "coin_type", optional=True),), pageable=False),
    CommandInfo("GetAddressCoinBalance", "Coin / Balance",
        (_a("owner", "owner"), _a("coin_type", "coin_type", optional=True)), pageable=False),
    CommandInfo("GetAddressCoinBalances", "Coin / Balance",
        (_a("owner", "owner"),), pageable=True),
    CommandInfo("GetCoins", "Coin / Balance",
        (_a("owner", "owner"), _a("coin_type", "coin_type", optional=True)), pageable=True),
    CommandInfo("GetGas", "Coin / Balance",
        (_a("owner", "owner"),), pageable=True),
    CommandInfo("GetCoinSummary", "Coin / Balance",
        (_a("coin_id", "coin_id"),), pageable=False),

    # Staking
    CommandInfo("GetStaked", "Staking",
        (_a("owner", "owner"),), pageable=True),
    CommandInfo("GetDelegatedStakes", "Staking",
        (_a("owner", "owner"),), pageable=True),

    # Objects
    CommandInfo("GetObject", "Objects",
        (_a("object_id", "object_id"),), pageable=False),
    CommandInfo("GetPastObject", "Objects",
        (_a("object_id", "object_id"), _a("version", "version")), pageable=False),
    CommandInfo("GetObjectSummary", "Objects",
        (_a("object_id", "object_id"),), pageable=False),
    CommandInfo("GetObjectContent", "Objects",
        (_a("object_id", "object_id"),), pageable=False),
    CommandInfo("GetObjectsOwnedByAddress", "Objects",
        (_a("owner", "owner"),), pageable=True),
    CommandInfo("GetObjectsForType", "Objects",
        (_a("owner", "owner"), _a("object_type", "object_type")), pageable=True),
    CommandInfo("GetMultipleObjects", "Objects",
        (_a("object_ids", "object_ids"),), pageable=False),
    CommandInfo("GetMultipleObjectSummary", "Objects",
        (_a("object_ids", "object_ids"),), pageable=False),
    CommandInfo("GetMultipleObjectContent", "Objects",
        (_a("object_ids", "object_ids"),), pageable=False),
    CommandInfo("GetMultiplePastObjects", "Objects",
        (_a("for_versions", "for_versions"),), pageable=False),
    CommandInfo("GetDynamicFields", "Objects",
        (_a("object_id", "object_id"),), pageable=True),

    # Epoch / Chain
    CommandInfo("GetBasicCurrentEpochInfo", "Epoch / Chain", (), pageable=False),
    CommandInfo("GetEpoch", "Epoch / Chain",
        (_a("epoch_id", "epoch_id", optional=True),), pageable=False),
    CommandInfo("GetLatestCheckpoint", "Epoch / Chain", (), pageable=False),
    CommandInfo("GetCheckpointBySequence", "Epoch / Chain",
        (_a("sequence_number", "sequence_number"),), pageable=False),
    CommandInfo("GetCheckpointByDigest", "Epoch / Chain",
        (_a("digest", "digest"),), pageable=False),
    CommandInfo("GetChainIdentifier", "Epoch / Chain", (), pageable=False),
    CommandInfo("GetLatestSuiSystemState", "Epoch / Chain", (), pageable=False),
    CommandInfo("GetProtocolConfig", "Epoch / Chain",
        (_a("version", "version", optional=True),), pageable=False),

    # Validators
    CommandInfo("GetCurrentValidators", "Validators", (), pageable=True),

    # Packages / Move
    CommandInfo("GetPackage", "Packages / Move",
        (_a("package", "package"),), pageable=True),
    CommandInfo("GetPackageVersions", "Packages / Move",
        (_a("package_address", "package_address"),), pageable=True),
    CommandInfo("GetModule", "Packages / Move",
        (_a("package", "package"), _a("module_name", "module_name")), pageable=False),
    CommandInfo("GetMoveDataType", "Packages / Move",
        (_a("package", "package"), _a("module_name", "module_name"), _a("type_name", "type_name")), pageable=False),
    CommandInfo("GetStructure", "Packages / Move",
        (_a("package", "package"), _a("module_name", "module_name"), _a("structure_name", "structure_name")), pageable=False),
    CommandInfo("GetStructures", "Packages / Move",
        (_a("package", "package"), _a("module_name", "module_name")), pageable=True),
    CommandInfo("GetFunction", "Packages / Move",
        (_a("package", "package"), _a("module_name", "module_name"), _a("function_name", "function_name")), pageable=False),
    CommandInfo("GetFunctions", "Packages / Move",
        (_a("package", "package"), _a("module_name", "module_name")), pageable=True),

    # Name Service
    CommandInfo("GetNameServiceAddress", "Name Service",
        (_a("name", "name"),), pageable=False),
    CommandInfo("GetNameServiceNames", "Name Service",
        (_a("owner", "owner"),), pageable=False),

    # Transactions
    CommandInfo("GetTransaction", "Transactions",
        (_a("digest", "digest"),), pageable=False),
    CommandInfo("GetTransactions", "Transactions",
        (_a("digests", "digests"),), pageable=False),
    CommandInfo("GetTransactionKind", "Transactions",
        (_a("digest", "digest"),), pageable=False),
]

COMMAND_LOOKUP: dict[str, CommandInfo] = {c.name: c for c in COMMAND_REGISTRY}
