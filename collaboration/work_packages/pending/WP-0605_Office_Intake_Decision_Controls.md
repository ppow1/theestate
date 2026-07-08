# WP-0605 - Office Intake Decision Controls

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first Office of the Steward decision controls for pending and blocked Orchestrator intake items.

WP-0603 creates the Orchestrator intake contract and file-backed intake queue. WP-0602 creates an Office activity panel for visibility. This package adds a bounded decision surface so the Steward can review pending or blocked intake items and record governed decisions without editing JSON files by hand.

This package does not implement scheduling or provider execution. It only implements Office-visible decision controls and local decision artifacts.

## Required Reading

Read these before implementation:

- `AI_START_HERE.md`
- `AI_HINTS.md`
- `docs/governance/Estate_Orientation_Handbook.md`
- `docs/governance/Estate_Manual.md`
- `docs/governance/Estate_Vision_and_Architecture.md`
- `docs/governance/Capability_Lifecycle_States_v1.md`
- `docs/governance/Practical_Worker_Onboarding_Addendum.md`
- `docs/collaboration/Estate_Collaboration_Layer_v1.md`
- `docs/collaboration/Estate_Collaboration_Standard_v1.md`
- `docs/architecture/execution_provider_operational_visibility_requirements.md`
- `docs/architecture/planning_pipeline.md`
- `collaboration/work_packages/pending/WP-0601_Operational_Event_Feed_and_Office_Status.md`
- `collaboration/work_packages/pending/WP-0602_Office_Operational_Activity_Panel.md`
- `collaboration/work_packages/pending/WP-0603_Orchestrator_Intake_Contract.md`

If WP-0601, WP-0602, or WP-0603 have already been implemented, inspect their actual files and integrate with them. Do not duplicate status readers, event writers, or intake queue logic.

## Architectural Intent

The Office of the Steward should become a live operational command center, not a static dashboard.

A visible blocked item is useful. A visible blocked item with a governed decision path is better.

This package should support this line:

`governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state`

Do not create a new office. Do not build the Orchestrator. Do not bypass Ingrid boundary requirements.

## Scope

Implement:

1. Office-side display of pending and blocked intake items.
2. Safe decision controls for allowed intake decisions.
3. Local decision artifact model.
4. Decision writer/helper.
5. Operational event emission or compatibility hook.
6. Intake status update after decision.
7. Tests for decision model, writer, and Office rendering.
8. Concise integration documentation.

## Allowed Decisions

Implement only these initial decision actions:

- `approve`
- `reject`
- `defer`
- `request_boundary_review`
- `mark_needs_revision`

Do not implement direct execution or scheduling.

## Out of Scope

Do not implement:

- scheduler,
- provider runner,
- automatic assignment,
- full Orchestrator,
- Codex Bridge,
- live provider dispatch,
- automatic email/calendar/contact actions,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new offices.

## Implementation Targets

Use existing repository conventions. Likely areas:

- existing Office of the Steward source directory,
- existing Office data loaders,
- existing Office action or local bridge mechanisms,
- `src/estate/core/orchestrator_intake.py` or equivalent if WP-0603 exists,
- `src/estate/core/operational_events.py` or equivalent if WP-0601 exists.

Preferred new core file if needed:

- `src/estate/core/orchestrator_intake_decisions.py`

Preferred tests:

- `tests/test_orchestrator_intake_decisions.py`
- Office component/action tests using existing test conventions.

Preferred documentation:

- `docs/integration/office_intake_decision_controls.md`

## Runtime Artifact Locations

Write decision artifacts under:

- `runtime/orchestrator/intake/decisions/<decision_id>.json`

Update or write status artifacts as appropriate:

- `runtime/orchestrator/intake/status/latest.json`
- `runtime/orchestrator/intake/status/queue.json`
- `runtime/operations/status/latest.json` if WP-0601 integration exists

Create runtime directories at runtime as needed.

## Decision Artifact Model

Implement and validate a decision artifact with these fields:

- `decision_id` string, required
- `intake_id` string, required
- `decision` string, required
- `decided_by` string, required
- `decided_at` ISO timestamp, required
- `reason` string, optional
- `classification` string, required
- `summary_safe` boolean, default false
- `next_state` string, required
- `requires_boundary_review` boolean, default false
- `requires_revision` boolean, default false
- `metadata` object, default empty

Allowed decisions:

- `approve`
- `reject`
- `defer`
- `request_boundary_review`
- `mark_needs_revision`

Allowed next states:

- `approved`
- `rejected`
- `deferred`
- `blocked`
- `needs_revision`

Allowed classifications:

- `Public`
- `Estate Internal`
- `Restricted`
- `Steward Only`
- `Local Only`

## Decision Semantics

- `approve`: marks intake approved for future scheduling, but does not schedule or execute it.
- `reject`: records that the intake should not proceed.
- `defer`: keeps the intake visible but not ready for immediate scheduling.
- `request_boundary_review`: records that Ingrid or the Boundary Office must review before proceeding.
- `mark_needs_revision`: records that the intake contract or work package must be revised.

Each decision must leave a durable artifact.

## Office Display Requirements

The Office surface should show:

- intake ID,
- work package ID or path,
- source,
- mission,
- safe summary,
- classification,
- priority,
- current intake state,
- boundary review requirement,
- approval requirement,
- validation requirement,
- available decisions,
- latest decision if present.

Sensitive summaries must be redacted by default unless marked safe.

## Office Action Requirements

Controls must be real.

Each exposed button/action must:

1. Call a real local handler or backend route.
2. Validate the requested decision.
3. Write a decision artifact.
4. Update intake status or queue artifacts.
5. Emit or prepare an operational event.
6. Display success, blocked, or failure result.

No fake controls. No placeholder success. No silent failure.

## CLI Fallback Requirement

If Office action plumbing is complex, implement a CLI fallback using existing Estate CLI conventions.

Preferred command:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat orchestrator-intake-decide --intake-id <id> --decision approve --decided-by Steward --reason "Approved for scheduling"
```

The Office may call the same underlying decision helper.

## Boundary Behavior

- Restricted, Steward Only, and Local Only intake summaries should be redacted unless summary-safe metadata exists.
- `approve` must not override boundary review requirements for Restricted or Steward Only items.
- If an item requires boundary review, the visible decision should prefer `request_boundary_review` unless metadata indicates review was completed.
- Decision artifacts must not include secrets, credentials, or raw private prompts.

## Operational Event Compatibility

If WP-0601 exists, emit decision events through the shared operational event feed.

Suggested event types:

- `Waiting for Approval`
- `Boundary Review Required`
- `Checkpoint Reached`
- `Result Returned`

If WP-0601 does not exist, write decision artifacts so a later bridge can emit events without redesign.

## Tests

Add tests covering:

1. Valid decision artifact accepted.
2. Unknown decision rejected.
3. Unknown classification rejected.
4. Approve writes decision artifact.
5. Reject writes decision artifact.
6. Defer writes decision artifact.
7. Boundary review decision writes decision artifact.
8. Needs revision decision writes decision artifact.
9. Intake queue/status updates after decision.
10. Sensitive summaries redacted by default.
11. Office rendering shows available decisions.
12. Office action or CLI fallback records a real decision.
13. Invalid decision exits non-zero or reports failure clearly.

Use existing repository test style.

## Documentation

Create `docs/integration/office_intake_decision_controls.md` with:

- purpose,
- decision model,
- allowed decisions,
- runtime artifact locations,
- Office behavior,
- CLI fallback command,
- boundary behavior,
- integration with WP-0603 intake,
- integration with WP-0601 operational events.

Keep it concise.

## Acceptance Criteria

Complete when:

- pending and blocked intake items are visible in the Office or documented Office-consumable surface,
- allowed decision controls exist,
- every exposed control performs a real local action,
- decision artifacts are written,
- intake status updates after decisions,
- sensitive content is redacted by default,
- tests pass,
- documentation exists,
- no scheduler or provider runner was implemented,
- no new office was created.

## Validation

Run targeted tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
python -m pytest tests/test_orchestrator_intake_decisions.py
.\estate.bat audit
```

If repository conventions require different commands, use those and report the actual commands.

Produce an implementation summary with:

- files changed,
- tests run,
- audit result,
- decision artifact path,
- Office behavior summary,
- blocked items,
- recommended follow-up package.

## Do Not Touch

Do not modify:

- archived institutional memory,
- Alfred responsibility definitions,
- Helen responsibility definitions,
- Ingrid responsibility definitions,
- provider execution code,
- scheduler code,
- unrelated Office surfaces.

## Expected Follow-On Packages

Do not implement these now:

- WP-0606 Orchestrator scheduling skeleton.
- WP-0607 Provider health checks and capacity reporting.
- WP-0608 Worker assignment board integration.
