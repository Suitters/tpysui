=========
Dashboard
=========

The Dashboard provides a live overview of the active wallet address,
including gas coin balances, owned objects, and current chain state.

Access with ``Ctrl+1`` or by selecting **Dashboard** in the sidebar.

.. contents:: Contents
   :depth: 2

.. image:: ./placeholder_dashboard.png
   :alt: tpysui Dashboard showing chain strip and three data panes

Chain Strip
-----------

The top bar of the Dashboard displays live chain information for the
active network connection:

- **Chain** — the chain identifier (e.g. ``35834a8a`` for Sui mainnet)
- **Epoch** — the current epoch number
- **Ref Gas** — the reference gas price in MIST
- **Validators** — the number of active validators

The chain strip refreshes whenever the active group, profile, or address
changes.

Gas Objects
-----------

The **Gas Objects** pane lists all ``0x2::sui::SUI`` coin objects owned
by the active address.

.. image:: ./placeholder_dashboard_gas.png
   :alt: tpysui Dashboard gas objects pane

Each row shows the truncated object ID and its balance in SUI. Hover over
a row to see the full object ID, version, and digest in a tooltip.

Owned Objects
-------------

The **Owned Objects** pane lists all other objects owned by the active
address (gas coins are excluded).

.. image:: ./placeholder_dashboard_objects.png
   :alt: tpysui Dashboard owned objects pane

Each row shows the truncated object ID. Hover over a row to see the full
object ID, type, version, and digest.

Coin Balances
-------------

The **Coin Balances** pane displays all coin types held by the active
address, including non-SUI coins, as a JSON summary.

.. image:: ./placeholder_dashboard_balances.png
   :alt: tpysui Dashboard coin balances pane

Refresh
-------

The Dashboard loads automatically when first shown. It refreshes whenever
the active configuration, group, profile, or address changes.
