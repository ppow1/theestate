# SERIES TASK WP-0051 — Mailbox Operations Center

## Codex Command
Read `collaboration/work_packages/pending/WP-0051_SERIES_mailbox_operations_center.md` and do exactly what it says.

## Mission
Add the Mailbox Operations Center view to the Office of the Steward so institutional mail, acknowledgements, and mailbox synchronization duties are visible from the main UI.

## Scope
Create an Operations Center tab or panel that reads existing mailbox artifacts where available:

- mailbox indexes
- mailbox synchronization duty reports
- Check for Updates reports
- Communication Bus messages
- personnel and mailbox resolver outputs

The view should show:

- mailbox summary by resident/office/worker
- unread or open messages
- acknowledgement-required messages
- messages waiting on the Steward
- unresolved or ambiguous destination warnings
- last mailbox synchronization time

## Behavior Requirements
- Use quiet refresh without full page redraws where feasible.
- Keep messages summarized by default, with detail expansion available.
- Respect global and per-topic verbosity principles from WP-0046.
- Surface mailbox counts into the bottom status bar where available.

## Constraints
Do not redesign mailboxes. Do not create new message authority. Do not mark messages read or acknowledged unless an existing safe mechanism supports it and the Steward explicitly acts. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering with no messages, open messages, acknowledgement-required messages, unresolved destination warnings, and missing mailbox artifacts.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0051_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
