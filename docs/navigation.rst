==========
Navigation
==========

tpysui uses a persistent sidebar for navigating between functional areas.
All areas are reachable at any time without losing context in other areas.

.. contents:: Contents
   :depth: 2

Sidebar
-------

The left sidebar lists the four functional areas of tpysui:

.. image:: ./left_nav.png
   :alt: tpysui sidebar showing four areas

1. **Dashboard** — wallet overview
2. **Configuration & Key Mgmt** — manage groups, profiles, and addresses
3. **Data Reads** — query on-chain data
4. **Utilities** — coin management, transfers, and development tools

Use the arrow keys to move between items in the sidebar, or use the
keyboard shortcuts below.

Keyboard Shortcuts
------------------

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Shortcut
     - Action
   * - ``Ctrl+1``
     - Switch to Dashboard
   * - ``Ctrl+2``
     - Switch to Configuration & Key Mgmt
   * - ``Ctrl+3``
     - Switch to Data Reads
   * - ``Ctrl+4``
     - Switch to Utilities
   * - ``Ctrl+Q``
     - Quit tpysui

Modal Dialogs
-------------

Many operations in tpysui open a modal dialog. All modals share the same
interaction pattern:

- ``Ctrl+S`` — confirm / save
- ``Escape`` — cancel and close without changes

Creating a New PysuiConfig
--------------------------

To create a new configuration:

1. From the startup dialog, select **New Config**, or use the Configuration
   & Key Mgmt area if you already have a config loaded.
2. A directory browser will open. Navigate to the folder where you want
   to store your configuration.
3. Enter a filename and press ``Ctrl+S`` to save.
4. tpysui creates the ``PysuiConfig.json`` file and loads it automatically.

.. image:: ./new_config.png
   :alt: tpysui new configuration dialog
