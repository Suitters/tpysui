=========
Utilities
=========

The Utilities area provides 11 built-in wallet operations covering coin
management, transfers, and development tools. Operations can be simulated
before committing to the chain.

Access with ``Ctrl+4`` or by selecting **Utilities** in the sidebar.

.. contents:: Contents
   :depth: 2

.. image:: ./placeholder_utilities.png
   :alt: tpysui Utilities screen showing group and command selectors

Selecting a Utility
-------------------

Two dropdowns at the top of the screen narrow the command list:

1. **Group** — choose a category: *Coin Management*, *Transfers*, or *Development*.
2. **Utility** — choose a command within that group.

Selecting a command enables the **Args...**, **Reset**, and (when ready) **Run** buttons.

Configuring Arguments
---------------------

Most utilities require arguments. After selecting a command:

1. Press **Args...** to open the argument collection dialog.
2. Fill in the required fields. Address and coin fields offer selection lists
   populated from the active configuration.
3. Press ``Ctrl+S`` to confirm. The status label changes to **Ready**.

The **Run** button is only enabled when all required arguments have been confirmed.
Press **Reset** to clear the current argument set and start over.

Running a Utility
-----------------

Press **Run** to open the confirmation dialog. The dialog shows a summary of
the arguments and offers three choices:

**Cancel**
    Close without executing.

**Simulate**
    Dry-run the transaction against the chain without committing any state
    changes. Useful for verifying gas cost and argument correctness.

**Execute**
    Submit the transaction to the chain.

.. note::
   **smash-coins** and **splay-coins** do not support Simulate because they
   merge all available coins in a single sweep; a partial dry-run would not
   reflect the real operation.

Results
-------

After execution the result panel displays:

- A status line showing **Simulated** or **Executed**, the transaction digest,
  and gas consumed in MIST.
- The full transaction result as formatted JSON.

Press **Copy** to copy the JSON to the clipboard, or **Save...** to write it
to a file using the directory browser.

Gas Options
-----------

Every utility exposes optional gas controls:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Argument
     - Description
   * - ``owner``
     - Signing address. Defaults to the active address when left blank.
   * - ``gas_mode``
     - *Use Gas Coin* (use the profile gas coin), *Use Account Balance*
       (draw from SUI balance), or *Auto Select* (let pysui choose).
   * - ``gas``
     - Specific coin objects to use for gas. Optional; overrides ``gas_mode``
       when provided.
   * - ``budget``
     - Maximum gas budget in MIST. Optional; pysui estimates when omitted.

Available Commands
------------------

Coin Management
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Command
     - Description
   * - ``merge-coin``
     - Merge one or more coins into a target coin.
   * - ``split-coin``
     - Split a coin into new coins of specified MIST amounts.
   * - ``split-coin-equally``
     - Split a coin into *N* equal parts.
   * - ``smash-coins``
     - Merge all SUI coins in the wallet into one. Cannot be simulated.
   * - ``splay-coins``
     - Distribute SUI across multiple coins or recipients. Cannot be simulated.
   * - ``coin-to-account``
     - Move a MIST amount from a coin object into the SUI account balance.
   * - ``account-to-coin``
     - Mint a new coin object from the SUI account balance.

Transfers
~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Command
     - Description
   * - ``transfer-object``
     - Transfer one or more owned objects to a recipient address.
   * - ``transfer-sui``
     - Transfer a MIST amount of SUI to a recipient from a single coin.
   * - ``pay-sui``
     - Split a coin and pay multiple recipients in a single transaction.

Development
~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Command
     - Description
   * - ``move-struct-to-bcs``
     - Generate Python BCS dataclasses from on-chain Move struct definitions.
       Uses a custom directive editor — see `move-struct-to-bcs`_ below.

move-struct-to-bcs
------------------

This command uses a dedicated editor rather than the standard argument dialog.
It generates Python BCS dataclass source files from on-chain Move struct layouts.

Directive File
~~~~~~~~~~~~~~

The editor works with a **directive file** — a JSON file that describes which
Move structs to generate code for and where to write the output files.

On first use, the launcher dialog offers two options:

**Load Existing...**
    Browse to an existing directive ``.json`` file. Its targets are loaded
    into the editor.

**Create New...**
    Open the editor with an empty target list. You will be prompted to save
    the directive file before running.

Editing Targets
~~~~~~~~~~~~~~~

Each **target** maps a Move struct to an output Python file:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Field
     - Description
   * - **Type**
     - ``Structure`` for a concrete struct; ``GenericStructure`` for a generic
       (parameterised) struct.
   * - **Move Structure**
     - Fully-qualified Move type tag, e.g. ``0x2::coin::Coin``.
   * - **Out file**
     - Absolute path to the ``.py`` file to generate. Use **…** to browse.

For ``GenericStructure`` targets, add one or more **generic params** (name →
type value pairs) that instantiate the type parameters.

Use **Add Target** to append the staged entry to the targets list.
Select a row in the targets table to load it back into the staging area for
editing, then press **Update**.

Saving the Directive
~~~~~~~~~~~~~~~~~~~~

Press **Save** (the button next to the Config File path) to persist the
directive JSON. The button turns green when the file is saved and current.
The directive must be saved before **OK** is pressed, and its path is passed
to the utility as the ``directive_file`` argument.

After pressing **OK** the Utilities screen returns to the Ready state
and **Run** becomes active.
