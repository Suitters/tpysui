====================================================================
tpysui — Terminal UI for PysuiConfiguration Management
====================================================================

A keyboard-driven console TUI for creating, editing, and managing
``PysuiConfig.json`` files used by the `pysui <https://github.com/FrankC01/pysui>`_
Sui blockchain SDK.

Features
--------

* Create new or open existing ``PysuiConfig.json`` files
* Add, edit, and delete Groups, Profiles, and Addresses
* Import existing Mysten Sui ``client.yaml`` into a group
* Query on-chain data with 44 built-in read commands
* Coin management utilities: merge, transfer, and split SUI

Installing ``tpysui`` will also install ``pysui`` and ``pysui-fastcrypto``
which requires having Rust installed. If you do not have Rust and don't want
to, or can't, install Rust see install notes in pysui_.

.. _pysui: https://github.com/FrankC01/pysui/blob/main/README.md#pysui-sdk-install

Install
-------

#. Activate, or create and activate, a virtual environment
#. Install ``tpysui`` using pip: :code:`pip install tpysui`
#. Run :code:`tpysui` from the command line

Clone
-----

``tpysui`` uses pipenv. If you have not installed it, do so first.

#. Clone the github repo
#. :code:`cd tpysui`
#. :code:`pipenv shell`
#. If needed, manually install ``pysui-fastcrypto``. See install notes in pysui_
#. :code:`pipenv install`
#. :code:`tpysui`

Documentation
-------------

See Documentation_ for full usage help.

.. _Documentation: https://github.com/suitters/tpysui/blob/main/docs/index.rst
