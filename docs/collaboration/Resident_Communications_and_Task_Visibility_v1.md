# Resident Communications and Task Visibility v1

This layer reuses existing personnel, mailbox, message, resident-presence, and Office status artifacts. It does not create a new communications institution, mailbox registry, task queue, scheduler, or dashboard.

## Status schema

Resident task status records use `resident_task_status.v1` and are stored at `runtime/residents/task_status.json`. The versioned schema is `data/schemas/resident_task_status_v1.json`.

Each visible row links a resident identity to an employee and mailbox identity, then exposes goal, current task, last meaningful movement, waiting-on, blocker, next action, next checkpoint, availability state, unread count, escalation state, stale-status flag, and source links.

## Governed messages

Resident-to-resident operational messages are ordinary `collaboration/messages/*.json` records with source and destination set to existing mailbox identities. Alfred, Helen, and the Steward are not used as the transport layer.

## Privacy

The Office participant board omits private journals, detailed workforce assessments, health notes, and confidential notes. Helen receives availability constraints only, not private workforce detail.

## Role-specific consumption examples

- Alfred consumes `alfred_attention_summary()` for concise attention items.
- Grace consumes `grace_operational_status()` for operational status only; this does not activate unauthorized roles.
- Helen consumes `helen_availability_constraints()` for assignment planning constraints without private assessment detail.
