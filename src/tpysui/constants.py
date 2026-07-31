#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

SUI_GQL_GROUP  = "sui_gql_config"
SUI_GRPC_GROUP = "sui_grpc_config"
SUI_USER_GROUP = "user"

GQL_STANDARD_PROFILES = [
    ("devnet",  "https://graphql.devnet.sui.io/graphql"),
    ("testnet", "https://graphql.testnet.sui.io/graphql"),
    ("mainnet", "https://graphql.mainnet.sui.io/graphql"),
]

GRPC_STANDARD_PROFILES = [
    ("devnet",       "fullnode.devnet.sui.io:443"),
    ("testnet",      "fullnode.testnet.sui.io:443"),
    ("mainnet",      "fullnode.mainnet.sui.io:443"),
    ("testnet-arch", "archive.testnet.sui.io:443"),
    ("mainnet-arch", "archive.mainnet.sui.io:443"),
]

NETWORK_TYPES = ["LOCAL", "DEVELOP", "TEST", "PRODUCTION"]

STANDARD_PROFILE_NETWORK_TYPES = {
    "devnet": "DEVELOP",
    "testnet": "TEST",
    "mainnet": "PRODUCTION",
    "testnet-arch": "TEST",
    "mainnet-arch": "PRODUCTION",
}
