============================
Configuration & Key Mgmt
============================

The Configuration & Key Mgmt area manages the full structure of a
``PysuiConfig.json`` file: groups, profiles (network endpoints), and
addresses (keys).

Access with ``Ctrl+2`` or by selecting **Configuration & Key Mgmt** in
the sidebar.

.. contents:: Contents
   :depth: 2

.. image:: ./placeholder_config.png
   :alt: tpysui Configuration & Key Mgmt screen

Overview
--------

A PysuiConfig is organized as a three-level hierarchy:

- **Groups** — named sets of profiles and addresses (e.g. ``sui_gql_config``)
- **Profiles** — network endpoint URLs within a group
- **Addresses** — key pairs (addresses) available within a group

Groups
------

Creating a Group
^^^^^^^^^^^^^^^^

Press ``Ctrl+A`` with focus in the Groups section, or use the **Add Group**
action. A dialog will prompt for the group name and protocol type (GraphQL
or gRPC). Standard Mysten profile URLs are populated automatically.

.. image:: ./placeholder_group_create.png
   :alt: tpysui create group dialog

Editing a Group
^^^^^^^^^^^^^^^

Select a group and press ``Ctrl+E`` to edit its name or active status.

Deleting a Group
^^^^^^^^^^^^^^^^

Select a group and press ``Ctrl+D`` or use the delete action. Deleting a
group removes all its profiles and addresses. The last remaining group
cannot be deleted.

Profiles
--------

Profiles are network endpoint URLs (GraphQL or gRPC) within a group.

Creating a Profile
^^^^^^^^^^^^^^^^^^

Press ``Ctrl+A`` with focus in the Profiles section. Enter the profile
name and URL in the dialog that appears.

.. image:: ./placeholder_profile_create.png
   :alt: tpysui create profile dialog

Editing and Deleting
^^^^^^^^^^^^^^^^^^^^

Select a profile and press ``Ctrl+E`` to edit, or ``Ctrl+D`` to delete.

Addresses
---------

Addresses represent key pairs (public/private keys) available for signing
transactions within a group.

Creating an Address
^^^^^^^^^^^^^^^^^^^

Press ``Ctrl+A`` with focus in the Addresses section. Choose a key scheme
(ED25519, SECP256k1, or SECP256r1) and optionally provide an alias.

.. image:: ./placeholder_address_create.png
   :alt: tpysui create address dialog

Editing and Deleting
^^^^^^^^^^^^^^^^^^^^

Select an address and press ``Ctrl+E`` to edit its alias or active status,
or ``Ctrl+D`` to delete it.
