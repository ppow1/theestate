# WP-0609 - Orchestrator Runtime Core

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first bounded Estate Orchestrator Runtime Core.

This package turns the intake, decision, schedule, provider catalog, provider health, assignment, and operational event primitives into a single local orchestration control loop that can evaluate work, select eligible scheduled items, create dispatch records, update assignment state, and emit operational events.

This is real Orchestrator work.

It is still not provider-specific execution. The Orchestrator coordinates, records, and dispatches to provider adapter contracts. Execution providers perform the actual work.

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
- `collaboration/work_packages/pending/WP-0606_Orchestrator_Scheduling_Skeleton.md`
- `collaboration/work_packages/pending/WP-0607_Provider_Health_and_Capacity_Reporting.md`
- `collaboration/work_packages/pending/WP-0608_Worker_Assignment_Board_Integration.md`

If any of WP-0601 through WP-0608 have already been implemented, inspect the actual code and integrate with it. Do not duplicate event feed, intake, decisions, schedule, provider catalog, provider health, or assignment board logic.

## Architectural Intent

The Orchestrator is the Estate's governed coordination runtime.

It must not become:

- Alfred,
- Helen,
- Ingrid,
- a provider,
- a worker,
- a new office,
- an uncontrolled agent,
- a browser automation layer,
- a hidden execution process.

The Orchestrator consumes institutional state, makes bounded routing decisions, produces durable orchestration artifacts, and emits visible lifecycle events.

The Orchestrator must support:

`governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state`

## Responsibility Boundary

Preserve this separation:

- Helen provisions workers.
- Operations or the Steward assigns and prioritizes work.
- Orchestrator evaluates and schedules eligible work.
- Orchestrator creates dispatch records.
- Execution Providers perform implementation.
- Planning Providers produce plans and work packages.
- Validation Providers prove behavior.
- Audit records trust evidence.
- Ingrid governs classification and boundary decisions.
- Office of the Steward displays state and decisions.

This package implements orchestration control and dispatch records. It does not invoke provider-specific tools.

## Scope

Implement:

1. Orchestrator runtime state model.
2. Orchestrator cycle result model.
3. Dispatch record model.
4. Dispatch queue artifacts.
5. A bounded single-cycle orchestrator command.
6. A dry-run mode.
7. Eligibility evaluation across intake, decisions, schedules, provider catalog, provider health, and assignments when available.
8. Dispatch creation for eligible scheduled items.
9. Blocked/deferred handling with reasons.
10. Assignment state update compatibility.
11. Operational event emission or compatibility hook.
12. Office-readable Orchestrator status artifacts.
13. Tests for orchestration cycle behavior, dispatch records, dry-run, and CLI behavior.
14. Concise integration documentation.

## Out of Scope

Do not implement:

- long-running daemon,
- background service installer,
- autonomous infinite loop,
- provider-specific execution,
- Codex invocation,
- ChatGPT invocation,
- Ollama invocation,
- network calls,
- credential handling,
- browser automation,
- automatic GitHub merge,
- Office UI changes,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new offices.

The command should run one explicit orchestration cycle and exit.

## Implementation Targets

Use existing repository conventions. Preferred files:

- `src/estate/core/orchestrator_runtime.py`
- `src/estate/core/orchestrator_dispatch.py`
- `src/estate/core/orchestrator_cycle.py`
- `tests/test_orchestrator_runtime.py`
- `tests/test_orchestrator_dispatch.py`
- `tests/test_orchestrator_cycle.py`
- `docs/integration/orchestrator_runtime_core.md`

If existing modules from WP-0603 through WP-0608 provide better shared models, extend them rather than duplicating them.

## Runtime Artifact Locations

Create runtime directories at runtime as needed:

- `runtime/orchestrator/runtime/status/latest.json`
- `runtime/orchestrator/runtime/status/summary.md`
- `runtime/orchestrator/runtime/cycles/`
- `runtime/orchestrator/dispatch/pending/`
- `runtime/orchestrator/dispatch/blocked/`
- `runtime/orchestrator/dispatch/deferred/`
- `runtime/orchestrator/dispatch/completed/`
- `runtime/orchestrator/dispatch/status/queue.json`

Do not commit empty runtime directories unless repository convention requires placeholders.

## Orchestrator Runtime State Model

Implement runtime state with these fields:

- `orchestrator_id` string, default `estate.orchestrator.local`
- `cycle_id` string, required
- `started_at` ISO timestamp, required
- `finished_at` ISO timestamp, optional
- `mode` string, required
- `state` string, required
- `items_evaluated` integer, default 0
- `dispatches_created` integer, default 0
- `items_blocked` integer, default 0
- `items_deferred` integer, default 0
- `events_emitted` integer, default 0
- `errors` list, default empty
- `warnings` list, default empty
- `metadata` object, default empty

Allowed modes:

- `dry_run`
- `single_cycle`

Allowed states:

- `idle`
- `running`
- `completed`
- `completed_with_warnings`
- `failed`

## Dispatch Record Model

Implement and validate dispatch records with these fields:

- `dispatch_id` string, required
- `created_at` ISO timestamp, required
- `created_by` string, default `estate.orchestrator.local`
- `cycle_id` string, required
- `state` string, required
- `intake_id` string, optional
- `schedule_id` string, optional
- `assignment_id` string, optional
- `work_package_id` string, optional
- `work_package_path` string, optional
- `provider_id` string, optional
- `provider_type` string, optional
- `required_capabilities` list, default empty
- `classification` string, required
- `priority` string, default `normal`
- `mission` string, required
- `summary` string, required
- `allowed_paths` list, default empty
- `forbidden_paths` list, default empty
- `expected_outputs` list, default empty
- `validation_required` boolean, default true
- `boundary_review_reference` string, optional
- `decision_reference` string, optional
- `blocked_reason` string, optional
- `deferred_reason` string, optional
- `artifact_paths` list, default empty
- `metadata` object, default empty

Allowed dispatch states:

- `pending_dispatch`
- `blocked`
- `deferred`
- `cancelled`

This package must not create `running` provider execution state. Execution providers own their own running/completed provider execution records.

## Orchestration Cycle Behavior

A single orchestration cycle should:

1. Load scheduled queue artifacts when available.
2. Load intake status artifacts when needed.
3. Load decision artifacts when needed.
4. Load provider catalog when available.
5. Load provider health/capacity when available.
6. Load assignment board when available.
7. Evaluate eligible scheduled items.
8. Create pending dispatch records for eligible items.
9. Create blocked or deferred dispatch records for ineligible items.
10. Update Orchestrator runtime status.
11. Update dispatch queue status.
12. Emit operational events when available.
13. Print concise cycle summary.

If upstream artifacts do not exist, the cycle should exit cleanly with a no-work summary rather than failing.

Malformed upstream artifacts should be reported as warnings or errors according to severity and should not silently disappear.

## Eligibility Rules

An item may become a pending dispatch when:

- it has a scheduled record or equivalent eligible scheduling state,
- required approvals are present,
- boundary requirements are satisfied,
- provider ID or type is known enough to dispatch,
- provider catalog does not mark provider deprecated or blocked,
- provider health does not mark provider blocked, offline, out_of_quota, or saturated unless metadata allows queueing while saturated,
- assignment state does not indicate completed, cancelled, failed, or blocked without override,
- classification is valid,
- work package path or executable artifact reference exists when required.

An item should become blocked when:

- approval is required but missing,
- boundary review is required but missing,
- provider is blocked or deprecated,
- classification is invalid,
- work package path is missing for work package execution,
- assignment state is blocked or needs revision.

An item should become deferred when:

- provider health is unknown,
- provider is busy or saturated but queueing is allowed,
- provider catalog is unavailable,
- capacity is unknown,
- deferred scheduling is explicitly requested.

Every blocked or deferred record must include a reason.

## CLI Requirements

Add commands using existing Estate CLI conventions.

Preferred commands:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat orchestrator-cycle --dry-run
.\estate.bat orchestrator-cycle --single
.\estate.bat orchestrator-dispatch-list
```

The cycle command must:

1. Run one explicit cycle.
2. Support dry-run without writing dispatch records.
3. Support single-cycle mode that writes dispatch records.
4. Print concise summary.
5. Exit zero when there is no work.
6. Exit non-zero for malformed command input or unrecoverable runtime errors.

The dispatch list command must:

1. Read dispatch queue artifacts.
2. Print pending, blocked, and deferred dispatch records.
3. Exit zero when queue is empty.

If existing CLI routing uses another pattern, follow it and document actual commands.

## Operational Event Compatibility

If WP-0601 exists, emit events through the shared operational event feed.

Suggested event types:

- `Job Accepted`
- `Checkpoint Reached`
- `Waiting for Approval`
- `Boundary Review Required`
- `Worker Blocked`
- `Result Returned`

If WP-0601 is not available, write cycle and dispatch artifacts so later event bridging is possible without redesign.

## Assignment Compatibility

If WP-0608 exists, Orchestrator should update or reference assignment state when dispatch records are created.

Do not create new worker identities.

Do not provision workers.

If assignment artifacts are unavailable, create dispatch records without assignment enrichment and record a warning.

## Provider Catalog and Health Compatibility

If WP-0604 exists, use it to validate provider and capability compatibility.

If WP-0607 exists, use it to avoid dispatching to providers that are blocked, offline, out_of_quota, or saturated unless queueing is allowed.

If either artifact is unavailable, defer when uncertainty affects safe dispatch.

## Boundary Behavior

- Scheduling and dispatch must not weaken classification.
- Restricted and Steward Only work must preserve boundary references.
- Do not print sensitive summaries unless metadata marks `summary_safe: true`.
- Dispatch records must not include credentials, tokens, raw private prompts, or private source material.

## Tests

Add tests covering:

1. Runtime state model validates.
2. Dispatch record model validates.
3. Dry-run with no work exits cleanly and writes no dispatch.
4. Single cycle with no work exits cleanly.
5. Eligible scheduled item creates pending dispatch.
6. Missing approval creates blocked dispatch.
7. Missing boundary review creates blocked dispatch.
8. Provider unavailable creates deferred dispatch.
9. Provider blocked creates blocked dispatch.
10. Unknown provider catalog creates deferred dispatch.
11. Dispatch queue status is written.
12. Runtime latest status is written.
13. Sensitive summaries are redacted by default.
14. CLI dry-run succeeds.
15. CLI single-cycle succeeds.
16. CLI dispatch-list succeeds with empty queue.
17. Malformed upstream artifact reports a clear error or warning.

Do not require network access.

## Documentation

Create `docs/integration/orchestrator_runtime_core.md` with:

- purpose,
- runtime state model,
- dispatch record model,
- cycle behavior,
- runtime artifact locations,
- CLI examples,
- eligibility rules,
- relationship to intake,
- relationship to decisions,
- relationship to scheduling,
- relationship to provider catalog,
- relationship to provider health,
- relationship to assignments,
- relationship to operational events,
- explicit statement that this package does not execute providers.

Keep it concise.

## Acceptance Criteria

Complete when:

- Orchestrator runtime state model exists,
- dispatch record model exists,
- one-cycle Orchestrator command works,
- dry-run mode works,
- dispatch queue artifacts are written,
- blocked/deferred reasons are recorded,
- Orchestrator latest status artifact is written,
- dispatch list command works,
- operational event compatibility exists,
- provider catalog/health compatibility is used when available,
- assignment compatibility is used when available,
- tests pass,
- documentation exists,
- no provider execution was implemented,
- no daemon or infinite loop was implemented,
- no new office was created.

## Validation

Run targeted tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
python -m pytest tests/test_orchestrator_runtime.py tests/test_orchestrator_dispatch.py tests/test_orchestrator_cycle.py
.\estate.bat audit
```

If repository conventions require different commands, use those and report actual commands.

Produce an implementation summary with:

- files changed,
- tests run,
- audit result,
- runtime status artifact paths,
- dispatch artifact paths,
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

- WP-0610 Execution Provider Adapter Contract.
- WP-0611 Office Orchestrator Control Panel.
- WP-0612 Orchestrator policy rules and priority management.
- WP-0613 Provider-specific dispatch adapters.
