# SERIES TASK WP-0092 — Operations Center Help and About

## Codex Command
Read `collaboration/work_packages/pending/WP-0092_SERIES_operations_center_help_and_about.md` and do exactly what it says.

## Mission
Implement the first Help and About surfaces for the Estate Operations Center so the Steward can inspect UI version, workspace capabilities, command availability, and local documentation links without leaving the control room.

## Scope
Build on the Operations Center Layout Framework, Workspace Profiles, Command Console, Service Catalog, and existing documentation registry.

The Help and About surfaces should expose:

- Operations Center UI version
- active workspace profile
- available panels and workspaces
- command console help
- service catalog links
- validation status links where available
- documentation links
- local-first / authority boundary notes
- known unavailable features

## Behavior Requirements
- Help and About are informational surfaces only.
- Do not become a new documentation source of truth.
- Link back to authoritative documents and implementation artifacts.
- Degrade gracefully when optional documentation or commands are unavailable.
- Support future expansion for tutorials and operator guidance.

## Constraints
Do not create new governance. Do not duplicate documentation content except for brief summaries. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify version display, documentation links, unavailable-feature handling, command help rendering, workspace/panel listing, and graceful missing-data behavior.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0092_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
