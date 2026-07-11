# WP-0524 Actionable Notification Contract

Status: installed by WP-0531. WP-0531 must perform any shared Office integration.

## Model

`NotificationEvidence` wraps existing notification evidence without claiming ownership of the source runtime. It carries source URI, creation time, severity, delivery status, delivery error, authoritative status, and opaque payload.

`ActionableNotification` adds Steward-local operational controls: acknowledgement, snooze, assignment, follow-up date, routing, source opening, action log, and persistence snapshot.

## Truth Boundaries

- Local acknowledgement records that the Steward has seen or triaged an item.
- Local acknowledgement does not close the source item.
- Authoritative closure requires a canonical source receipt.
- Delivery failures escalate attention even when the item is not old.
- Invalid actions return blocked states instead of pretending success.

## Controls

- `acknowledge`: records local acknowledgement and preserves authoritative state.
- `snooze`: blocks past dates; stores a future snooze target.
- `assign`: blocks empty assignees; records the assignee.
- `schedule_follow_up`: blocks past dates; records a follow-up target.
- `route`: blocks empty destinations; records routing intent and reason.
- `open_source`: returns the canonical source URI for evidence review.
- `close_authoritatively`: requires a source receipt before marking closure.
- `attention_indicators`: reports aging, escalation, delivery failure, and blocked state.
- `refresh`: deterministically merges updated evidence while preserving local state.

## Conflict Surface

Installation must reconcile with WP-0519 and existing notification runtimes. This staged module must not replace runtime delivery ownership, source closure ownership, Office action registration, or UI tab registration until WP-0531.
