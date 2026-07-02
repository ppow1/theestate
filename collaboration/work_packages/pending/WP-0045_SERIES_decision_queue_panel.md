# SERIES TASK WP-0045 — Decision Queue Panel

## Codex Command
Read `collaboration/work_packages/pending/WP-0045_SERIES_decision_queue_panel.md` and do exactly what it says.

## Mission
Add the first Steward Decision Queue panel to the Office of the Steward so decisions requiring Steward attention are visible in one place.

## Scope
Implement a local dashboard panel that can display decision items from existing artifacts where available:

- Steward Recall Decision Model
- Notification Router reports
- Alfred operational briefing
- Morning Briefing
- work package blockers
- mailbox messages requiring acknowledgement

Each decision item should include:

- title
- reason
- requested_by
- source artifact/path
- urgency
- recommended action
- status

## Behavior Requirements
- Use real data where existing reports provide it.
- Show clear placeholder/empty state when no decisions are pending.
- Do not create new authority or automatically approve decisions.
- Do not notify the Steward from this package.

## Constraints
Local-first only. Do not add external services. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`. Do not make generated panel output authoritative.

## Tests
Verify the panel renders with no decisions, with representative decisions, and with missing source artifacts.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0045_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
