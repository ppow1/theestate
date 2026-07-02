# SERIES TASK WP-0047 — Status Bar and Activity Console

## Codex Command
Read `collaboration/work_packages/pending/WP-0047_SERIES_status_bar_activity_console.md` and do exactly what it says.

## Mission
Implement the first persistent status bar and collapsible activity console for the Estate Operations Center.

## Scope
Add a bottom status bar that remains visible across the Operations Center and displays current operational indicators such as:

- Estate status
- Last refresh time
- Validation state
- Pending decisions
- Mailbox count
- Active workers
- Version

Add a collapsible activity console that can show recent operational activity without requiring a full page refresh.

## Activity Console Requirements
- Can be collapsed/expanded.
- Shows timestamp, source, topic, severity, and message.
- Supports quiet background refresh.
- Does not blink or redraw the full page.
- Includes a basic verbosity selector using the UI principles from WP-0046.
- Provides clear empty and missing-data states.

## Constraints
Local-first only. Do not implement external notification transport. Do not create final logging policy. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify status bar rendering, activity console expand/collapse behavior, quiet refresh behavior where testable, and graceful missing-data handling.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0047_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
