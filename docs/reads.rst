==========
Data Reads
==========

The Data Reads area provides access to 44 built-in on-chain query commands
covering objects, balances, events, transactions, and more.

Access with ``Ctrl+3`` or by selecting **Data Reads** in the sidebar.

.. contents:: Contents
   :depth: 2

.. image:: ./placeholder_reads.png
   :alt: tpysui Data Reads screen showing command list and result pane

Command List
------------

A dropdown at the top of the screen lists all available read commands.
Select a command from the dropdown to make it active.

Running a Command
-----------------

Some commands require no arguments and can be run immediately by pressing
the **Run** button.

Commands that require arguments must be configured first:

1. Select the command in the list.
2. Press **Args** to open the argument collection dialog.

.. image:: ./placeholder_reads_args.png
   :alt: tpysui Data Reads argument collection dialog

3. Fill in the required fields. Address and object ID fields offer
   selection lists populated from the active configuration.
4. Press ``Ctrl+S`` to confirm the arguments.
5. Press **Run** to execute the command.

The **Run** button is only enabled after arguments have been confirmed
at least once for commands that require them.

Results
-------

Query results are displayed in the right panel as formatted JSON.

.. image:: ./placeholder_reads_results.png
   :alt: tpysui Data Reads result pane with JSON output

Saving Results
--------------

Press **Save** to write the current result to a file. A directory browser
will open to choose the save location and filename.

Available Commands
------------------

Coin / Balance
~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ``GetCoinMetaData``
     - Fetch metadata for a specific coin type.
   * - ``GetAddressCoinBalance``
     - Fetch the total balance for a specific coin type owned by an address.
   * - ``GetAddressCoinBalances``
     - Fetch all coin-type balances for an address.
   * - ``GetCoins``
     - Fetch all coin objects of a specific type owned by an address.
   * - ``GetGas``
     - Fetch all SUI gas coin objects owned by an address.
   * - ``GetCoinSummary``
     - Fetch coin object summary (balance and metadata without content).

Staking
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ``GetStaked``
     - Fetch all staked SUI coin objects owned by an address.
   * - ``GetDelegatedStakes``
     - Fetch all delegated-stake (StakedSui) objects owned by an address.

Objects
~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ``GetObject``
     - Fetch the current state of a single object.
   * - ``GetPastObject``
     - Fetch a specific version of an object.
   * - ``GetObjectSummary``
     - Fetch a thin summary (id, version, digest, owner) for a single object.
   * - ``GetObjectContent``
     - Fetch BCS content for a single object.
   * - ``GetObjectsOwnedByAddress``
     - Fetch all objects owned by an address.
   * - ``GetObjectsForType``
     - Fetch all objects of a specific type owned by an address.
   * - ``GetMultipleObjects``
     - Fetch the current state of multiple objects by ID list.
   * - ``GetMultipleObjectSummary``
     - Fetch thin summaries (id, version, digest, owner) for a list of objects.
   * - ``GetMultipleObjectContent``
     - Fetch BCS content for multiple objects.
   * - ``GetMultiplePastObjects``
     - Fetch specific versions of multiple objects.
   * - ``GetDynamicFields``
     - Fetch dynamic fields of an object.

Epoch / Chain
~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ``GetBasicCurrentEpochInfo``
     - Fetch the minimal current epoch fields needed for gas and expiry building.
   * - ``GetEpoch``
     - Fetch epoch information by ID, or the current epoch if no ID is given.
   * - ``GetLatestCheckpoint``
     - Fetch the latest checkpoint.
   * - ``GetCheckpointBySequence``
     - Fetch a checkpoint by sequence number.
   * - ``GetCheckpointByDigest``
     - Fetch a checkpoint by digest.
   * - ``GetChainIdentifier``
     - Return the chain identifier (network genesis checkpoint digest) as a string.
   * - ``GetLatestSuiSystemState``
     - Fetch the current Sui system state summary.
   * - ``GetProtocolConfig``
     - Fetch protocol configuration for a specific version or current.

Validators
~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ``GetCurrentValidators``
     - Fetch all currently active validators (GQL paging handled via execute_for_all).

Packages / Move
~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ``GetPackage``
     - Fetch a Move package by ID.
   * - ``GetPackageVersions``
     - Fetch all versions of a Move package sharing the same original ID.
   * - ``GetModule``
     - Fetch a Move module's structure and function definitions.
   * - ``GetMoveDataType``
     - Fetch a Move struct or enum by name.
   * - ``GetStructure``
     - Fetch a specific Move struct by name.
   * - ``GetStructures``
     - Fetch all structs in a Move module (auto-paginated on GraphQL).
   * - ``GetFunction``
     - Fetch a specific Move function by name.
   * - ``GetFunctions``
     - Fetch all functions in a Move module (auto-paginated on GraphQL).

Name Service
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ``GetNameServiceAddress``
     - Resolve a Sui name-service name to an address.
   * - ``GetNameServiceNames``
     - Resolve an address to its Sui name-service name(s).

Transactions
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ``GetTransaction``
     - Fetch a single transaction by digest.
   * - ``GetTransactions``
     - Fetch multiple transactions by digest list.
   * - ``GetTransactionKind``
     - Fetch the transaction kind for a single transaction by digest.
   * - ``SimulateTransaction``
     - Simulate a serialized transaction (BCS bytes or base64 string).

Verification
~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Command
     - Description
   * - ``VerifyTransactionSignature``
     - Verify a transaction signature (intent scope = TransactionData).
   * - ``VerifyPersonalMessageSignature``
     - Verify a personal message signature (intent scope = PersonalMessage).
