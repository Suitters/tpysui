#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Modal dialogs package."""

from .configfm import ConfigSaver, ConfigPicker, ConfigGener, GenSpec
from .confirm import NewKey, ConfirmDeleteRowDialog, OkPopup
from .pyconfig_add import (
    AddGroup,
    AddProfile,
    AddIdentity,
    NewGroup,
    NewIdentity,
    NewProfile,
)
from .single_choice import SingleChoiceDialog
from .pyconfig_new import NewConfiguration, NewConfig, InjectGroup, InjectConfig
from .pyconfig_popup import PopUpMenu, ButtonStatic

__all__ = [
    "ConfigSaver",
    "ConfigPicker",
    "ConfigGener",
    "GenSpec",
    "NewKey",
    "ConfirmDeleteRowDialog",
    "OkPopup",
    "AddGroup",
    "NewGroup",
    "AddProfile",
    "NewProfile",
    "AddIdentity",
    "NewIdentity",
    "SingleChoiceDialog",
    "NewConfiguration",
    "NewConfig",
    "InjectGroup",
    "InjectConfig",
    "PopUpMenu",
    "ButtonStatic",
]
