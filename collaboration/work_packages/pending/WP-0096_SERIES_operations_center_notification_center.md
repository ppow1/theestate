# SERIES TASK WP-0096 — Operations Center Notification Center

## Codex Command
Read `collaboration/work_packages/pending/WP-0096_SERIES_operations_center_notification_center.md` and do exactly what it says.

## Mission
Implement the Operations Center Notification Center as the centralized Steward-facing surface for reviewing operational notifications from existing Estate systems without creating a parallel notification source.

## Scope
Build on the Operations Center Layout Framework, Status Bar, Operator Activity Stream, Service Health Registry, Validation Metrics, Mission Control, mailbox events, HR events, and existing Notification Center concepts.

The Notification Center should aggregate existing notification-like artifacts where available, including:

- service health warnings
- validation observations and defects
- worker/runtime alerts
- Mission Control recommendations
- mailbox or HR notices
- Steward recall state
- operations readiness warnings
- completion/review-ready signals

The interface should support:

- read/unread or acknowledged/unacknowledged state where appropriate
- severity levels
- filtering by source/subsystem
- links to authoritative artifacts
- quiet refresh
- integration with the Operations Center Status Bar
- integration with the Operator Activity Stream

## Behavior Requirements
- The Notification Center is an aggregator, not the authoritative source.
- Do not fabricate notifications.
- Missing upstream data should show as unavailable, not fail.
- Notifications must link back to source artifacts where available.
- Acknowledgment state must not mutate authoritative source events unless an existing convention already supports that.
- Respect operator verbosity and filter settings where available.
- Preserve Steward authority boundaries and recall semantics.

## Constraints
Do not create a new notification transport. Do not send external notifications. Do not duplicate Gotify or recall behavior. Do not bypass existing Notification Router semantics. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify aggregation from available sources, missing-source handling, severity filtering, acknowledgment behavior, status bar integration, activity stream integration, source-link integrity, and quiet refresh behavior.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0096_codex_done.json` using the standard completion schema.

## Merge Class
Class A unless notification authority, external delivery, or recall semantics are changed; escalate to Class B if governance semantics are altered.
