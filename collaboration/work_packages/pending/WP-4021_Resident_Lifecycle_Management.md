# WP-4021 — Resident Lifecycle Management

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4003, WP-4004, WP-4005, WP-4013, WP-4016
Classification: Estate Internal

## Objective

Implement the complete governed lifecycle for Estate residents from candidate intake through hiring, onboarding, active service, reflection, continuity refresh, stand-down, reassignment, retirement, archival, and possible succession.

## Required Implementation

Create one reusable lifecycle state machine using existing personnel, resident, workforce, mailbox, continuity, authority, and audit systems.

Required states:

```text
candidate
under_review
approved_for_hire
onboarding
ready_for_service
active
reflection_due
in_reflection
stand_down
reassignment_review
retirement_review
retired
archived
successor_review
```

Requirements:

- Every transition must define actor, authority, prerequisites, evidence, output, and rollback or correction behavior.
- Preserve Steward-reserved appointments and constitutional approvals.
- Integrate Helen hiring, workforce, cognitive-health, and continuity workflows.
- Integrate Ingrid privacy and classification requirements.
- Integrate mailbox and employee identity creation through existing registries.
- Preserve one resident identity across reflection and continuity refresh.
- Distinguish refreshed resident, retired resident, and true successor.
- Support lifecycle status, history, pending gate, and next-action CLI commands.
- Add existing Office status and detail integration.
- Create deterministic transition tests, including invalid, duplicate, interrupted, and resumed transitions.

## Deliverables

- resident lifecycle state machine and local records;
- versioned lifecycle schemas;
- CLI and Office integration;
- migration or compatibility handling for Alfred, Helen, and Grace records;
- tests and local demonstration;
- `operations/validation/reports/WP-4021_resident_lifecycle_management.md`;
- `collaboration/work_packages/completions/WP-4021_codex_done.json`.

## Boundaries

Do not create duplicate personnel, resident, mailbox, continuity, or authority registries. Do not auto-appoint, auto-retire, or auto-create successors. Do not treat reflection as identity replacement.

## Acceptance Criteria

- lifecycle transitions are deterministic and authority-checked;
- invalid transitions are rejected;
- interrupted transitions can resume safely;
- identity persists across continuity refresh;
- retirement and succession remain distinct;
- Office status is truthful and source-linked;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4021_Resident_Lifecycle_Management.md and do exactly what it says.
```
