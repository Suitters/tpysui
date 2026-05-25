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
