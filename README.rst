====================================================================
tpysui — Terminal UI for PysuiConfiguration Management
====================================================================

A keyboard-driven console TUI for creating, editing, and managing
``PysuiConfig.json`` files used by the `pysui <https://github.com/FrankC01/pysui>`__
Sui blockchain SDK.

Features
--------

* Four-area TUI layout: Dashboard, Configuration & Key Management, Data Reads, and Utilities
* Wallet Dashboard with chain strip, gas, objects, and balances panes
* Data-driven command taxonomy with 44 read commands and dynamic arg collection
* 10 wallet utility commands with Simulate/Execute workflow
* ``move-struct-to-bcs`` directive support with dedicated launch and edit modals
* Command and utility descriptions displayed in select dropdowns
* Version banner displayed in top-right of app

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
