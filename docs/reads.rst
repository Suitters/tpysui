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

The left panel lists all available read commands grouped by category.
Select a command to see its description and required arguments.

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
