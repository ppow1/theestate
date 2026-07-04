# SERIES TASK WP-0081 — Estate Service Catalog

## Codex Command
Read `collaboration/work_packages/pending/WP-0081_SERIES_estate_service_catalog.md` and do exactly what it says.

## Mission
Create an Estate Service Catalog that inventories operational services exposed by the Estate and maps them to their owning offices, capabilities, interfaces, and operational status.

## Scope
Aggregate existing services and commands without becoming the source of truth, including HR services, Mission Control, validation, notifications, mailbox operations, worker management, and future Alfred orchestration.

## Behavior Requirements
- Read-only aggregation.
- Link every service to authoritative implementation and owning office.
- Record command aliases where available.
- Surface readiness and validation state.
- Support future Operations Center integration.

## Constraints
Do not create duplicate command registries. Do not invent services. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify service discovery, owner mapping, missing metadata handling, and source link integrity.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0081_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
