#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

import re

from pysui.sui.sui_bcs.bcs import TypeTag
from pysui.sui.sui_common.validators import valid_sui_address as _pysui_valid_sui_address


def valid_sui_address(v: str) -> bool:
    return _pysui_valid_sui_address(v)


def valid_type_tag(v: str) -> bool:
    try:
        TypeTag.type_tag_from(v)
        return True
    except Exception:
        return False


def valid_move_identifier(v: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", v))


def valid_base58(v: str) -> bool:
    return bool(re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]+", v))


def valid_unsigned_int(v: str) -> bool:
    return v.isdigit()


def suggest_network_type(url: str) -> str:
    """Suggest a NETWORK_TYPES value by matching well-known Sui URL patterns.

    Returns "LOCAL" as the default when no known pattern matches.
    """
    lowered = url.lower()
    if "localhost" in lowered or "127.0.0.1" in lowered:
        return "LOCAL"
    if "devnet" in lowered:
        return "DEVELOP"
    if "testnet" in lowered:
        return "TEST"
    if "mainnet" in lowered:
        return "PRODUCTION"
    return "LOCAL"
