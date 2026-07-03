# SERIES TASK WP-0050 — Office Navigation and Layout Framework

## Codex Command
Read `collaboration/work_packages/pending/WP-0050_SERIES_office_navigation_layout_framework.md` and do exactly what it says.

## Mission
Implement the first coherent navigation and layout framework for the Office of the Steward / Estate Operations Center.

## Scope
Create the structural UI shell that holds the Office together:

- collapsible left navigation panel
- top tabbed workspace
- main content region
- persistent bottom status bar integration point
- collapsible activity console integration point
- route/view placeholders for current and future Office areas

Initial navigation areas should include:

- Home
- Alfred
- Helen
- Daily Board
- Active Projects
- Expansion Roadmap
- Parking Lot
- Work Packages
- Mailboxes
- Validation
- Search
- Settings
- About

## Behavior Requirements
- Navigation panel must be collapsible.
- Tabs must allow switching views without crowding every panel onto one screen.
- Missing or not-yet-implemented panels should show clear placeholders.
- Layout should follow the UI principles from WP-0046.
- Do not require a polished visual design.

## Constraints
Local-first only. Do not add cloud services. Do not add authentication in this package. Do not replace CLI tools. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify layout renders, navigation items exist, tabs switch to expected views/placeholders, and missing panels degrade gracefully.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0050_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
