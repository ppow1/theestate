# WP-4017 — Office Resident Task Board

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4011, WP-4016
Classification: Estate Internal

## Objective

Implement the Office of the Steward participant task board so the Steward can see what each resident is doing without interrupting them.

## Required Implementation

Expose, for each authorized resident or worker:

- current goal;
- current task;
- task owner;
- last meaningful movement;
- waiting on;
- blocker;
- next action;
- next checkpoint;
- elapsed time;
- availability state;
- related work package or project;
- source artifact and last-updated timestamp.

Requirements:

- Reuse existing resident status, assignment, mailbox, operations, and Office surfaces.
- Provide machine-readable board data and a real Office UI view.
- Support filtering by resident, office, project, status, blocker, and staleness.
- Distinguish active work, waiting, blocked, paused, completed, and stale.
- Show truthful unknown or unavailable state rather than fabricating progress.
- Add refresh and detail navigation through existing Office action transport.
- Preserve minimum-necessary privacy; do not display journal bodies or protected workforce detail.
- Add CLI inspection and deterministic tests.

## Deliverables

- board aggregation service;
- versioned board schema;
- Office UI integration;
- CLI integration;
- tests for stale status, filtering, source linkage, privacy, and navigation;
- `operations/validation/reports/WP-4017_office_resident_task_board.md`;
- `collaboration/work_packages/completions/WP-4017_codex_done.json`.

## Boundaries

Do not create a second task queue, scheduler, assignment registry, command center, or resident transport layer. The board is an operational visibility surface, not the source of task authority.

## Acceptance Criteria

- the Steward can see current resident work and blockers;
- every status is timestamped and source-linked;
- stale or missing updates are obvious;
- detail navigation works;
- protected workforce content does not leak;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4017_Office_Resident_Task_Board.md and do exactly what it says.
```
