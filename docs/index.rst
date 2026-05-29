====================================================
tpysui — Terminal UI for PysuiConfiguration Management
====================================================

tpysui is a terminal user interface for creating, editing, and managing
**PysuiConfiguration** files used by the `pysui <https://github.com/frankc01/pysui>`_
Sui blockchain SDK. It provides a keyboard-driven console interface without
requiring manual JSON editing.

.. contents:: Contents
   :depth: 2

Requirements
------------

- Python 3.10.6 or later
- `pysui <https://pypi.org/project/pysui/>`_ >= 1.0.0

Installation
------------

::

    pip install tpysui

Running
-------

::

    tpysui

Startup
-------

On first run, or when no default configuration is found, tpysui presents
a startup dialog.

.. image:: ./placeholder_startup.png
   :alt: tpysui startup dialog — New Config or Open Existing

Two options are available:

**New Config**
    Create a new ``PysuiConfig.json`` file in a directory you choose.

**Open Existing**
    Browse to and open an existing ``PysuiConfig.json`` file.

Documentation
-------------

- `Navigation <navigation.rst>`_ — sidebar, keyboard shortcuts, and PysuiConfig creation
- `Dashboard <dashboard.rst>`_ — wallet overview: chain info, gas, objects, balances
- `Configuration & Key Management <config.rst>`_ — groups, profiles, and addresses
- `Data Reads <reads.rst>`_ — query on-chain data with built-in commands
- `Utilities <utilities.rst>`_ — coin management, transfers, and development tools
