# SERIES TASK WP-0054 — Global Search and Command Palette

## Codex Command
Read `collaboration/work_packages/pending/WP-0054_SERIES_global_search_command_palette.md` and do exactly what it says.

## Mission
Implement the first unified Global Search and Command Palette for the Estate Operations Center.

## Scope
Provide a searchable command interface and global search capable of discovering existing Estate artifacts without duplicating their underlying logic.

Search domains should include:
- Work Packages
- Missions
- Mailboxes
- Residents
- Daily Board
- Parking Lot
- Validation artifacts
- Documentation

Command Palette should support launching existing operations through registered commands while remaining local-first.

## Behavior Requirements
- Keyboard accessible.
- Search updates incrementally.
- Respect verbosity and UI principles from WP-0046.
- Gracefully report unavailable commands.

## Constraints
Do not invent AI interpretation in this package. Execute only existing commands. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify search across representative artifacts, command lookup, empty results, and unavailable command handling.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0054_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
