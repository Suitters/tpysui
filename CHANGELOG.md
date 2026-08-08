# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-08-08

### Added

- [enhancement](https://github.com/Suitters/tpysui/issues/10) Support pysui 1.3.0 network_type on profiles

### Fixed

### Changed

### Removed

## [1.0.0] - 2026-06-08

This release is a complete rewrite that refactored the entire codebase. It introduces support for pysui 1.0.0 and pysui-fastcrypto 0.7.3.

### Added

- Four-area TUI layout: Dashboard, Configuration & Key Management, Data Reads, and Utilities
- Wallet Dashboard with chain strip, gas, objects, and balances panes
- Data-driven command taxonomy (`pysui_commands.json`) with 44 read commands and dynamic `ArgsModal` arg collection
- 10 wallet utility commands (`pysui_utilities.json`) with Simulate/Execute workflow
- `move-struct-to-bcs` directive support with dedicated launch and edit modals
- Command and utility descriptions displayed in select dropdowns
- Version banner displayed in top-right of app
- Screenshots and updated documentation

### Fixed

### Changed

- Complete rewrite: new `src/` layout, service layer with DTO firewall, Textual 8.x framework
- "Data Writes" renamed to "Utilities"
- Replaced hardcoded command registry with taxonomy-driven architecture

### Removed

- Legacy command registry (`command_registry.py`) and hardcoded `_COMMAND_MAP` / `_make_arg_widget` approach

## [0.4.1] - 2025-10-16

### Added

### Fixed

- [bug](https://github.com/Suitters/tpysui/issues/8) Create erronesously nested under if statement.

### Changed

### Removed

## [0.4.0] - 2025-10-02

### Added

- Command key options for operations.
- Support for Mysten GraphQL BETA changes

### Fixed

### Changed

- Documentation now includes command keys.

### Removed

## [0.3.1] - 2025-08-04

### Added

### Fixed

- [bug](https://github.com/Suitters/tpysui/issues/5) Inject gRPC or GraphQL ignores cancel on dialog

### Changed

### Removed

## [0.3.0] - 2025-08-03

**BREAKING CHANGE** Triggering editing a cell in a configuration table has changed from the "e" key to "ctrl+e".

### Added

- [enhancement](https://github.com/Suitters/tpysui/issues/2) Generate GraphQL or gRPC standard groups

### Fixed

- [bug](https://github.com/Suitters/tpysui/issues/3) Exception attempting edit (`e`) on empty table
- [bug](https://github.com/Suitters/tpysui/issues/4) Deleting more than one row in same table throws exception

### Changed

- In 'New Identity' dialog, a Select dropdown for keys replaced the RadioSet.
- Editing a configuration cell now is triggered by "ctrl+e" instead of just "e".

### Removed

## [0.2.0] - 2025-07-03

### Added

- [enhancement](https://github.com/Suitters/tpysui/issues/1) Support Mysten client.yaml management

### Fixed

### Changed

### Removed

## [0.1.2] - 2025-06-29

### Added

### Fixed

- Main application execution script

### Changed

### Removed

## [0.1.1] - 2025-06-29

### Added

### Fixed

- Link to documentation

### Changed

### Removed

## [0.1.0] - 2025-06-29

Initial release!
