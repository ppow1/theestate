# WP-0519 - Mailbox, Notifications, and Attention Control Center

Status: Proposed
Priority: High
Owner: Chief Architect #5
Classification: Estate Internal

## Mission

Make communication and attention surfaces serviceable from the Office.

## Required Controls

- open message details;
- acknowledge locally;
- mark read or unread where supported;
- route or reply through canonical communication mechanisms;
- open sender and recipient personnel details;
- clear resolved local attention;
- inspect delivery failures;
- filter, search, and sort;
- refresh mailbox and notification state.

## Boundaries

Reuse existing mailbox, communication, notification, delivery, and acknowledgement mechanisms. Do not create a second mailbox system, notification bus, attention registry, or delivery queue.

## Functional Standard

Every action must invoke a canonical handler, update real state or durable evidence, refresh the relevant Office payload, and render truthful completed, blocked, or failed results.

## Testing

Prove browser-to-handler-to-state-to-render behavior for open, acknowledge, read/unread, route/reply, personnel navigation, attention clearing, delivery-failure inspection, filtering, and refresh.

## Acceptance Criteria

1. Mailbox and notification pages are operational.
2. Message and attention state changes persist.
3. Routing and replies use canonical communication paths.
4. Delivery failures are visible and actionable.
5. Local acknowledgement is not confused with authoritative source closure.
6. Focused tests and WP-0519 validation pass.

## Completion Receipt

```text
collaboration/work_packages/completions/WP-0519_codex_done.json
```

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-0519_Mailbox_Notifications_and_Attention_Control_Center.md and do exactly what it says.
```
