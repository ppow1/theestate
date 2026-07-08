# WP-0603 - Orchestrator Intake Contract

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first Orchestrator intake contract for Estate work requests.

This package does not implement the full Orchestrator. It creates the durable intake model, queue artifacts, validation rules, CLI intake command, and tests that future Operations, planning providers, execution providers, and the Office of the Steward can use to hand work into the future Orchestrator safely.

The goal is to create the front door for governed work, not the scheduler behind it.

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
- `docs/collaboration/Local_Execution_Adapter_Protocol_v1.md`
- `docs/architecture/planning_pipeline.md`
- `docs/architecture/execution_provider_operational_visibility_requirements.md`
- `collaboration/work_packages/pending/WP-0600_Planning_Provider_Framework.md`
- `collaboration/work_packages/pending/WP-0601_Operational_Event_Feed_and_Office_Status.md`

## Architectural Intent

Create a stable request envelope for work entering future Orchestrator control.

The Estate needs a way to represent work before scheduling decisions are made. That intake artifact must preserve governance, classification, provider requirements, validation expectations, and Steward visibility.

This package should support this line:

`governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state`

Do not turn this package into a scheduler, provider runner, or new office.

## Responsibility Separation

Preserve this separation:

- Helen provisions workers.
- Operations assigns or moves work.
- Orchestrator schedules execution.
- Planning Providers produce plans, drafts, and work packages.
- Execution Providers perform implementation work.
- Validation Providers prove behavior.
- Audit records trust evidence.
- Ingrid governs boundary and classification.
- Office of the Steward displays state and decisions.

This package implements intake only.

## Scope

Implement:

1. Orchestrator intake request model.
2. Intake status model.
3. Intake validation rules.
4. File-backed pending intake queue.
5. File-backed accepted/blocked intake records.
6. CLI command to submit intake requests from JSON.
7. CLI command to list intake queue state.
8. Operational event emission or compatibility hook for WP-0601.
9. Tests for intake validation, queue writes, blocked requests, and CLI behavior.
10. Concise integration documentation.

## Out of Scope

Do not implement:

- scheduling algorithm,
- provider execution,
- worker provisioning,
- automatic assignment,
- full Orchestrator service,
- Office UI changes,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new offices,
- live network calls.

## Implementation Targets

Use existing repository conventions. Preferred files:

- `src/estate/core/orchestrator_intake.py`
- `src/estate/core/orchestrator_intake_runtime.py`
- `tests/test_orchestrator_intake.py`
- `tests/test_orchestrator_intake_runtime.py`
- `docs/integration/orchestrator_intake_contract.md`

If existing modules already provide queue or runtime helpers, reuse them rather than creating duplicates.

## Runtime Artifact Locations

Create runtime directories at runtime as needed:

- `runtime/orchestrator/intake/pending/`
- `runtime/orchestrator/intake/accepted/`
- `runtime/orchestrator/intake/blocked/`
- `runtime/orchestrator/intake/status/latest.json`
- `runtime/orchestrator/intake/status/queue.json`

Do not commit empty runtime directories unless repository convention requires placeholders.

## Intake Request Model

Implement and validate an intake request envelope with these fields:

- `intake_id` string, required
- `created_at` ISO timestamp, required
- `requested_by` string, required
- `source` string, required
- `source_artifact` string, optional
- `work_package_id` string, optional
- `work_package_path` string, optional
- `assignment_id` string, optional
- `requested_worker_id` string, optional
- `requested_provider_type` string, optional
- `requested_provider_id` string, optional
- `classification` string, required
- `priority` string, default `normal`
- `state` string, default `pending`
- `mission` string, required
- `summary` string, required
- `required_capabilities` list, default empty
- `allowed_paths` list, default empty
- `forbidden_paths` list, default empty
- `expected_outputs` list, default empty
- `validation_required` boolean, default true
- `approval_required` boolean, default false
- `boundary_review_required` boolean, default false
- `budget_source` string, optional
- `metadata` object, default empty

Allowed classification values:

- `Public`
- `Estate Internal`
- `Restricted`
- `Steward Only`
- `Local Only`

Allowed priority values:

- `low`
- `normal`
- `high`
- `urgent`

Allowed initial state values:

- `pending`
- `accepted`
- `blocked`
- `rejected`

Allowed source examples:

- `manual`
- `planning_provider`
- `codex`
- `office`
- `alfred`
- `worker`

Do not fail merely because a new source string appears, but preserve it and document it.

## Intake Status Model

Implement intake status with these fields:

- `intake_id`
- `state`
- `created_at`
- `updated_at`
- `requested_by`
- `source`
- `work_package_id`
- `work_package_path`
- `requested_provider_type`
- `requested_provider_id`
- `classification`
- `priority`
- `mission`
- `summary`
- `validation_required`
- `approval_required`
- `boundary_review_required`
- `blocked_reason`
- `artifact_paths`
- `metadata`

## Validation Rules

Fail invalid intake requests for:

- missing `intake_id`,
- missing `created_at`,
- missing `requested_by`,
- missing `source`,
- missing `classification`,
- unknown classification,
- missing `mission`,
- missing `summary`,
- unknown priority,
- invalid initial state.

Block, rather than fail, requests when:

- classification is `Restricted` and `boundary_review_required` is false,
- classification is `Steward Only` and explicit approval metadata is absent,
- requested provider type is missing for a request that clearly requires execution,
- work package path is absent when source is `work_package`.

Blocked records must explain the reason.

## CLI Requirements

Add commands using existing Estate CLI conventions.

Preferred commands:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat orchestrator-intake-submit --request <path-to-intake-json>
.\estate.bat orchestrator-intake-list
```

Submit command must:

1. Load intake JSON.
2. Validate fields.
3. Decide pending vs blocked.
4. Write intake artifact.
5. Write latest status.
6. Update queue status.
7. Emit or prepare an operational event compatible with WP-0601.
8. Print concise summary.
9. Exit non-zero on invalid input.
10. Exit zero for blocked intake if the block is a valid governed outcome, but print BLOCKED clearly.

List command must:

1. Read queue/status artifacts.
2. Print pending and blocked intake items.
3. Exit zero when queue is empty.

If existing CLI routing uses another pattern, follow it and document the actual commands.

## Operational Event Compatibility

If WP-0601 has been implemented, use its operational event helpers to emit intake events.

If WP-0601 is not available yet, write an intake-local event/status artifact that can later be bridged without redesign.

Suggested event types:

- `Job Accepted`
- `Boundary Review Required`
- `Waiting for Approval`
- `Worker Blocked`

## Boundary Behavior

This is not full Ingrid enforcement, but it must preserve boundary decisions.

- Restricted requests should require boundary review.
- Steward Only requests should require explicit approval metadata.
- Blocked intake must be visible as blocked, not silently discarded.
- Sensitive summaries should not be printed in full unless metadata marks `summary_safe: true`.

## Tests

Add tests covering:

1. Valid intake request accepted.
2. Missing required field fails.
3. Unknown classification fails.
4. Unknown priority fails.
5. Restricted request without boundary review is blocked.
6. Steward Only request without approval metadata is blocked.
7. Pending intake artifact is written.
8. Blocked intake artifact is written.
9. Latest status artifact is written.
10. Queue status artifact is written.
11. CLI submit succeeds for valid intake.
12. CLI submit fails for invalid intake.
13. CLI submit clearly reports blocked intake.
14. CLI list succeeds with empty queue.
15. CLI list reports pending and blocked items.

Do not require network access.

## Documentation

Create `docs/integration/orchestrator_intake_contract.md` with:

- purpose,
- intake model,
- status model,
- runtime artifact locations,
- validation and block behavior,
- CLI examples,
- relationship to planning providers,
- relationship to execution providers,
- relationship to operational event feed,
- future Orchestrator notes.

Keep it concise.

## Acceptance Criteria

Complete when:

- intake model exists in code,
- intake validation exists,
- pending queue artifacts are written,
- blocked intake artifacts are written,
- latest and queue status artifacts are written,
- CLI submit command works,
- CLI list command works,
- tests pass,
- documentation exists,
- no scheduler or provider runner was implemented,
- no new office was created,
- future Orchestrator can consume intake artifacts without redesign.

## Validation

Run targeted tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
python -m pytest tests/test_orchestrator_intake.py tests/test_orchestrator_intake_runtime.py
.\estate.bat audit
```

If repository conventions require different commands, use those and report the actual commands.

Produce an implementation summary with:

- files changed,
- tests run,
- audit result,
- blocked items,
- recommended follow-up package.

## Do Not Touch

Do not modify:

- archived institutional memory,
- Alfred responsibility definitions,
- Helen responsibility definitions,
- Ingrid responsibility definitions,
- provider execution code,
- Codex Bridge implementation files except for import compatibility,
- Office UI components.

## Expected Follow-On Packages

Do not implement these now:

- WP-0604 Provider Registration and Capability Discovery.
- WP-0605 Office decision controls for pending/blocked intake.
- WP-0606 Orchestrator scheduling skeleton.
