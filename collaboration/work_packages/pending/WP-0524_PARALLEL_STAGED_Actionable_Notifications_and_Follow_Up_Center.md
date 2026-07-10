# WP-0524 - Actionable Notifications and Follow-Up Center

## Codex Command
Read collaboration/work_packages/pending/WP-0524_PARALLEL_STAGED_Actionable_Notifications_and_Follow_Up_Center.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Build a staged actionable-notification center that lets the Steward acknowledge, snooze, assign, follow up, route, and open related evidence through canonical mechanisms.

## Required Capabilities
- actionable notification model over existing notification evidence;
- acknowledge, snooze, assign, follow-up date, route, and open-source controls;
- delivery-failure visibility;
- attention aging and escalation indicators;
- no confusion between local acknowledgement and authoritative closure;
- deterministic refresh and persistence.

## Staging Requirements
Create under `collaboration/workstreams/WP-0524/`:

```text
install_manifest.json
staged/office_actionable_notifications.py
staged/test_office_actionable_notifications.py
actionable_notification_contract.md
validation_notes.md
rollback_notes.md
```

Do not edit shared active Office files. WP-0531 is the required install handoff.

## Conflict Surface
Expected final targets include a dedicated notification-control module, Office tab/action registration, tests, and docs. Declare overlaps with WP-0519 and existing notification runtimes.

## Validation
Prove acknowledgement, snooze, assignment, follow-up, routing, aging, delivery failure, persistence, and truthful blocked states.

## Completion Receipt
Create `collaboration/work_packages/completions/WP-0524_codex_done.json` and state that staged work is not installed work.
