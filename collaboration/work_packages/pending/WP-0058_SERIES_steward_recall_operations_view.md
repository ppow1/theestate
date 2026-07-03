# SERIES TASK WP-0058 — Steward Recall Operations View

## Codex Command
Read `collaboration/work_packages/pending/WP-0058_SERIES_steward_recall_operations_view.md` and do exactly what it says.

## Mission
Add the Steward Recall Operations View to the Estate Operations Center so recall requests, approvals, delivery results, and acknowledgement state are visible from the Steward's office.

## Scope
Create an Operations Center view or panel that reads existing recall artifacts where available:

- Steward Recall Decision Model
- Notification Router reports
- Gotify delivery reports
- Recall Audit Log
- Notification Center workspace outputs
- Morning Briefing recall sections

The view should show:

- active recall requests
- recall reason
- requested_by / originating worker
- Alfred decision state
- transport used
- delivery result
- acknowledgement state
- timestamp
- related source artifact links

## Behavior Requirements
- Clearly separate recall requests from ordinary notifications.
- Show recall lifecycle stages without inventing authority.
- Do not send or approve recalls unless an existing safe mechanism supports it and the Steward explicitly acts.
- Surface active recall count into the status bar where available.
- Respect UI principles from WP-0046.

## Constraints
Do not bypass Alfred. Do not implement new notification transports. Do not create escalation timers. Do not change constitutional authority. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering for no recalls, active recall, delivered recall, failed delivery, acknowledged recall, missing artifacts, and unknown acknowledgement state.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0058_codex_done.json` using the standard completion schema.

## Merge Class
Class A unless authority semantics change; escalate to Class B if recall authority is altered.
