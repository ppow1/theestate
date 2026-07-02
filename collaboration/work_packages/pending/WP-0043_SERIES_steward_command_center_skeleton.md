# SERIES TASK WP-0043 — Steward Command Center Skeleton

## Codex Command
Read `collaboration/work_packages/pending/WP-0043_SERIES_steward_command_center_skeleton.md` and do exactly what it says.

## Mission
Create the first local Office of the Steward as a lightweight web interface that brings together existing Estate capabilities.

## Scope
Implement a minimal local dashboard (for example on localhost) that displays existing operational information without replacing the CLI.

Initial panels:
- Alfred resident card
- Helen resident card
- Morning Briefing placeholder
- Steward Decision Queue placeholder
- Mailbox summary
- Work Package pipeline
- Validation status

The dashboard should consume existing reports where available and display clear placeholders where functionality is not yet implemented.

## Constraints
Keep it local-first. Do not require authentication, cloud services, or a polished UI. Do not duplicate business logic already implemented elsewhere. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify the dashboard starts locally, renders each panel, and degrades gracefully when supporting artifacts are missing.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0043_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
