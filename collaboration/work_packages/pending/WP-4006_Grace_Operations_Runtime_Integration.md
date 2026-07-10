# WP-4006 — Grace Operations Runtime Integration

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4005
Classification: Estate Internal

## Objective

Integrate Grace into the Estate as the governed operational executive for approved work, preserving the operating stack:

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.
```

## Required Scope

Implement Grace-facing contracts for:

- operational objective intake;
- current-state assessment;
- dependency and blocker analysis;
- next-action proposal;
- ownership and checkpoint assignment;
- Traffic Controller movement request;
- Dispatch handoff request;
- exception escalation;
- closure and reconciliation review.

Add Grace status to existing Office and operations surfaces without creating a second command center.

## Required Behaviors

- Grace acts decisively inside delegated authority.
- Recommendations, runtime state, and validation remain evidence rather than authority.
- Technical design remains with Engineering.
- Workforce assessment remains with Helen.
- Privacy and classification remain with Ingrid.
- Provider execution remains behind Dispatch and adapters.
- Institutional acceptance remains with authorized Chief Architect and Steward layers.

## Deliverables

- core Grace operational contracts and local store;
- versioned schemas;
- CLI and existing Office surface integration;
- tests for sequencing, blockers, checkpointing, escalation, and closure;
- `operations/validation/reports/WP-4006_grace_operations_runtime.md`;
- `collaboration/work_packages/completions/WP-4006_codex_done.json`.

## Boundaries

Do not create a parallel queue, event loop, scheduler, provider path, authority system, or Office UI. Do not let Grace merge code, appoint personnel, override Traffic Controller, or declare institutional acceptance.

## Acceptance Criteria

- approved work can be converted into a clear governed next action;
- ownership, dependency, and checkpoint are explicit;
- blocked or unauthorized movement escalates correctly;
- no provider execution or queue bypass occurs;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4006_Grace_Operations_Runtime_Integration.md and do exactly what it says.
```
