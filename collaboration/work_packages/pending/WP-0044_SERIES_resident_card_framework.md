# SERIES TASK WP-0044 — Resident Card Framework

## Codex Command
Read `collaboration/work_packages/pending/WP-0044_SERIES_resident_card_framework.md` and do exactly what it says.

## Mission
Create the reusable Resident Card framework for the Office of the Steward so Alfred, Helen, and future Estate residents share a common visual and data model.

## Scope
Implement a generic resident card component and backing model. Initially support Alfred and Helen with placeholders for future residents.

Each card should display:
- Name
- Role
- Operational status
- Current duty
- Mailbox
- Last activity
- Needs Steward (Yes/No)
- Link to resident details

Consume existing runtime data where available and show graceful placeholders otherwise.

## Constraints
Keep the implementation local-first. Reuse existing runtime information instead of duplicating logic. Do not add authentication, cloud dependencies, or new governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering with populated data and missing data, and confirm cards remain extensible for future residents.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0044_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
