# SERIES TASK WP-0076 — Estate Capability Registry

## Codex Command
Read `collaboration/work_packages/pending/WP-0076_SERIES_estate_capability_registry.md` and do exactly what it says.

## Mission
Create an Estate Capability Registry that inventories implemented capabilities, their providers, maturity, dependencies, and operational status without becoming the source of truth.

## Scope
Aggregate existing capability information from implemented subsystems, Mission Control, Operations Center, workers, validation, and service adapters.

Display and expose:
- capability name
- owning subsystem
- implementation status
- maturity (planned, partial, operational)
- dependencies
- validation status
- source artifact links

## Behavior Requirements
- Read-only aggregation.
- Gracefully handle missing metadata.
- Support future search and Mission Control integration.

## Constraints
Do not duplicate implementation logic. Do not create governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify capability discovery, missing metadata handling, dependency display, and authoritative source links.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0076_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
