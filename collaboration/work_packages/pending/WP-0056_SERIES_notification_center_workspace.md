# SERIES TASK WP-0056 — Notification Center Workspace

## Codex Command
Read `collaboration/work_packages/pending/WP-0056_SERIES_notification_center_workspace.md` and do exactly what it says.

## Mission
Add the first Notification Center workspace to the Estate Operations Center so recalls, informational notifications, delivery results, and alert history have a visible home.

## Scope
Create an Operations Center tab or panel that reads existing notification and recall artifacts where available:

- Notification Router reports
- Gotify delivery reports
- Recall Audit Log
- Steward Recall Decision Model outputs
- Morning Briefing recall summaries
- validation warnings that are surfaced as notifications

The workspace should show:

- active recalls
- notification history
- delivery status
- source worker/resident
- reason
- priority
- acknowledgement state where available
- source artifact links where available

## Behavior Requirements
- Clearly separate active recalls from informational notifications.
- Do not send notifications from this workspace unless an existing safe mechanism supports it and the Steward explicitly acts.
- Use quiet refresh without full-page redraws where feasible.
- Respect UI principles from WP-0046.
- Surface active recall count into the bottom status bar where available.

## Constraints
Do not implement new transport providers. Do not bypass Alfred or the Notification Router. Do not create escalation timers. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering with no notifications, active recall, informational notification, delivery failure, missing source artifacts, and acknowledgement unavailable states.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0056_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
