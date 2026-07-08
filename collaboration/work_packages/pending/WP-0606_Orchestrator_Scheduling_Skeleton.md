# WP-0606 - Orchestrator Scheduling Skeleton

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first bounded Orchestrator scheduling skeleton.

This package creates the minimum local scheduling layer that can move approved intake items toward scheduled execution records without running providers directly.

This is not the full Orchestrator. It is the scheduling skeleton: queue inspection, eligibility checks, scheduling records, state transitions, operational events, and tests.

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
- `collaboration/work_packages/pending/WP-0601_Operational_Event_Feed_and_Office_Status.md`
- `collaboration/work_packages/pending/WP-0603_Orchestrator_Intake_Contract.md`
- `collaboration/work_packages/pending/WP-0604_Provider_Registration_and_Capability_Discovery.md`
- `collaboration/work_packages/pending/WP-0605_Office_Intake_Decision_Controls.md`

If WP-0601 through WP-0605 have already been implemented, inspect the actual code and integrate with it. Do not duplicate intake, event, decision, or provider-catalog logic.

## Architectural Intent

Create the first scheduling layer without turning the Orchestrator into an execution provider.

The Orchestrator schedules. Providers execute. Validation proves. Office displays. Steward decides.

This package must support:

`governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state`

The scheduler should only create scheduled execution records and update state. It should not invoke Codex, ChatGPT, Ollama, Python jobs, PowerShell jobs, GitHub Actions, or any other provider.

## Scope

Implement:

1. Schedule request/record model.
2. Scheduler eligibility checks.
3. File-backed scheduled queue.
4. File-backed deferred queue.
5. File-backed blocked scheduling records.
6. CLI command to schedule eligible approved intake.
7. CLI command to list scheduled/deferred/blocked items.
8. Operational event emission or compatibility hook.
9. Provider catalog compatibility checks when available.
10. Tests for scheduling, blocking, deferring, and CLI behavior.
11. Concise integration documentation.

## Out of Scope

Do not implement:

- provider execution,
- Codex invocation,
- ChatGPT invocation,
- Ollama invocation,
- worker provisioning,
- long-running daemon,
- production scheduler loop,
- automatic queue polling service,
- Office UI changes,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new offices.

## Implementation Targets

Use existing repository conventions. Preferred files:

- `src/estate/core/orchestrator_scheduler.py`
- `src/estate/core/orchestrator_schedule_runtime.py`
- `tests/test_orchestrator_scheduler.py`
- `tests/test_orchestrator_schedule_runtime.py`
- `docs/integration/orchestrator_scheduling_skeleton.md`

If existing files from WP-0603 or WP-0605 provide better shared models, extend those rather than duplicating them.

## Runtime Artifact Locations

Create directories at runtime as needed:

- `runtime/orchestrator/schedule/scheduled/`
- `runtime/orchestrator/schedule/deferred/`
- `runtime/orchestrator/schedule/blocked/`
- `runtime/orchestrator/schedule/status/latest.json`
- `runtime/orchestrator/schedule/status/queue.json`

Do not commit empty runtime directories unless repository convention requires placeholders.

## Schedule Record Model

Implement and validate a schedule record with these fields:

- `schedule_id` string, required
- `intake_id` string, required
- `created_at` ISO timestamp, required
- `updated_at` ISO timestamp, required
- `scheduled_by` string, required
- `state` string, required
- `priority` string, required
- `classification` string, required
- `work_package_id` string, optional
- `work_package_path` string, optional
- `assignment_id` string, optional
- `provider_type` string, optional
- `provider_id` string, optional
- `required_capabilities` list, default empty
- `allowed_paths` list, default empty
- `forbidden_paths` list, default empty
- `expected_outputs` list, default empty
- `validation_required` boolean, default true
- `boundary_review_required` boolean, default false
- `approval_reference` string, optional
- `decision_reference` string, optional
- `blocked_reason` string, optional
- `deferred_until` ISO timestamp, optional
- `artifact_paths` list, default empty
- `metadata` object, default empty

Allowed states:

- `scheduled`
- `deferred`
- `blocked`
- `cancelled`

Allowed priorities:

- `low`
- `normal`
- `high`
- `urgent`

Allowed classifications:

- `Public`
- `Estate Internal`
- `Restricted`
- `Steward Only`
- `Local Only`

## Eligibility Rules

A schedule attempt may create a scheduled record only when:

- intake exists,
- intake is approved or otherwise explicitly marked eligible by existing decision metadata,
- classification is valid,
- required boundary review is satisfied or not required,
- requested provider or provider type is available or can be deferred for later provider selection,
- validation expectations are preserved,
- no forbidden path conflicts are obvious from the intake envelope.

A schedule attempt must create a blocked record when:

- intake is missing,
- intake is rejected,
- intake needs revision,
- boundary review is required but not completed,
- approval is required but not recorded,
- classification is invalid,
- provider requirements conflict with available provider catalog evidence,
- work package path is missing for work-package-based execution.

A schedule attempt may create a deferred record when:

- intake is valid but requested provider is unavailable,
- provider catalog is unavailable,
- requested capacity is not currently known,
- deferred scheduling is explicitly requested.

Blocked and deferred records must explain why.

## CLI Requirements

Add commands using existing Estate CLI conventions.

Preferred commands:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat orchestrator-schedule --intake-id <id>
.\estate.bat orchestrator-schedule-list
```

Optional request-file form:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat orchestrator-schedule --request <path-to-schedule-request-json>
```

Schedule command must:

1. Load intake and decision artifacts as needed.
2. Validate eligibility.
3. Create scheduled, deferred, or blocked schedule record.
4. Update schedule queue status.
5. Emit or prepare operational event.
6. Print concise summary.
7. Exit zero for governed scheduled/deferred/blocked outcomes.
8. Exit non-zero only for malformed input, missing files, or runtime errors.

List command must:

1. Read scheduled/deferred/blocked status artifacts.
2. Print concise summary.
3. Exit zero when no scheduled items exist.

If existing CLI routing uses another pattern, follow it and document actual commands.

## Provider Catalog Compatibility

If WP-0604 provider catalog exists, scheduler should use it to check:

- provider ID exists,
- provider type matches,
- required capabilities are available,
- classification ceiling is compatible,
- provider status is not deprecated or blocked.

If provider catalog does not exist yet, defer rather than fail when provider availability cannot be determined.

## Operational Event Compatibility

If WP-0601 exists, emit scheduling events through the shared operational event feed.

Suggested event types:

- `Job Accepted`
- `Checkpoint Reached`
- `Waiting for Approval`
- `Boundary Review Required`
- `Worker Blocked`

If WP-0601 is not available, write schedule artifacts so a later bridge can emit events without redesign.

## Boundary Behavior

- Restricted and Steward Only schedule records must preserve boundary review and approval references.
- Do not print sensitive summaries unless metadata marks `summary_safe: true`.
- Scheduling must not weaken classification.
- Scheduling must not execute anything.

## Tests

Add tests covering:

1. Valid approved intake schedules successfully.
2. Missing intake blocks or fails clearly according to repository convention.
3. Rejected intake creates blocked schedule record.
4. Needs-revision intake creates blocked schedule record.
5. Restricted intake without boundary review creates blocked record.
6. Approved intake with unavailable provider creates deferred record.
7. Provider catalog capability mismatch creates blocked or deferred record with reason.
8. Scheduled artifact written.
9. Deferred artifact written.
10. Blocked artifact written.
11. Queue status artifact written.
12. CLI schedule works for approved intake.
13. CLI schedule clearly reports blocked intake.
14. CLI list succeeds with empty queue.
15. CLI list reports scheduled/deferred/blocked items.

Do not require network access.

## Documentation

Create `docs/integration/orchestrator_scheduling_skeleton.md` with:

- purpose,
- schedule record model,
- eligibility rules,
- runtime artifact paths,
- CLI examples,
- relationship to intake decisions,
- relationship to provider catalog,
- relationship to operational events,
- explicit statement that this does not execute providers.

Keep it concise.

## Acceptance Criteria

Complete when:

- schedule record model exists,
- eligibility checks exist,
- scheduled/deferred/blocked artifacts are written,
- queue status artifacts are written,
- CLI schedule command works,
- CLI list command works,
- provider catalog compatibility is used or safely deferred,
- operational event compatibility exists,
- tests pass,
- documentation exists,
- no provider execution was implemented,
- no new office was created.

## Validation

Run targeted tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
python -m pytest tests/test_orchestrator_scheduler.py tests/test_orchestrator_schedule_runtime.py
.\estate.bat audit
```

If repository conventions require different commands, use those and report actual commands.

Produce an implementation summary with:

- files changed,
- tests run,
- audit result,
- schedule artifact paths,
- blocked or deferred cases,
- recommended follow-up package.

## Do Not Touch

Do not modify:

- archived institutional memory,
- Alfred responsibility definitions,
- Helen responsibility definitions,
- Ingrid responsibility definitions,
- provider execution code,
- Office UI components,
- unrelated runtime queues.

## Expected Follow-On Packages

Do not implement these now:

- WP-0607 Provider health checks and capacity reporting.
- WP-0608 Worker assignment board integration.
- WP-0609 Execution dispatch adapter contract.
