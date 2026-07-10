# WP-4011 — Resident Communications and Task Visibility

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4003, WP-4006
Classification: Estate Internal

## Objective

Give the Steward and authorized residents a truthful view of current resident work and a governed way to exchange operational messages without using the Steward as the message bus.

## Required Scope

Extend existing mailbox, message, resident-presence, and Office status systems to expose:

- resident goal;
- current task;
- last meaningful movement;
- waiting on;
- blocker;
- next action;
- next checkpoint;
- availability state;
- unread message count;
- escalation state.

Implement:

- resident status records linked to existing employee and mailbox identities;
- governed resident-to-resident messages through existing communication mechanisms;
- concise Alfred attention summaries;
- Grace operational status consumption;
- Helen workforce-availability constraints;
- privacy-safe Office of the Steward participant board;
- stale-status detection;
- deterministic tests and CLI inspection.

## Required Outputs

- versioned resident task-status schema;
- existing Office participant/task-board integration;
- communication examples for Alfred, Helen, and Grace without activating unauthorized roles;
- tests for stale state, mailbox identity, privacy, and escalation;
- `operations/validation/reports/WP-4011_resident_communications_task_visibility.md`;
- `collaboration/work_packages/completions/WP-4011_codex_done.json`.

## Boundaries

Do not create a new communications institution, mailbox registry, task queue, scheduler, or operations dashboard. Do not expose private journals or detailed workforce assessments. Do not make Alfred, Helen, or the Steward the transport layer. Reuse existing message, mailbox, runtime, and Office surfaces.

## Acceptance Criteria

- the Steward can see who is doing what without interrupting the resident;
- every visible status is timestamped and source-linked;
- stale or missing status is reported truthfully;
- residents can exchange governed messages without bypassing authority;
- private workforce details remain protected;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4011_Resident_Communications_and_Task_Visibility.md and do exactly what it says.
```
