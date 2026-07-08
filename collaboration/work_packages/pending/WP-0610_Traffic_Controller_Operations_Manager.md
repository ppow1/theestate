# WP-0610 - Traffic Controller / Operations Manager

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first Traffic Controller / Operations Manager layer for the Estate.

The Orchestrator is the mechanical coordination runtime. The Traffic Controller / Operations Manager is the personnel and operations role that decides how work should move through that machinery.

This package creates the first implementation surface for operational work control: prioritization, assignment recommendations, queue review, hold/release decisions, cancellation/defer decisions, escalation flags, and Steward-visible operational summaries.

This package does not implement provider execution and does not replace Alfred, Helen, Ingrid, or the Orchestrator.

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
- `docs/architecture/planning_pipeline.md`
- `docs/architecture/execution_provider_operational_visibility_requirements.md`
- `collaboration/work_packages/pending/WP-0601_Operational_Event_Feed_and_Office_Status.md`
- `collaboration/work_packages/pending/WP-0603_Orchestrator_Intake_Contract.md`
- `collaboration/work_packages/pending/WP-0604_Provider_Registration_and_Capability_Discovery.md`
- `collaboration/work_packages/pending/WP-0605_Office_Intake_Decision_Controls.md`
- `collaboration/work_packages/pending/WP-0606_Orchestrator_Scheduling_Skeleton.md`
- `collaboration/work_packages/pending/WP-0607_Provider_Health_and_Capacity_Reporting.md`
- `collaboration/work_packages/pending/WP-0608_Worker_Assignment_Board_Integration.md`
- `collaboration/work_packages/pending/WP-0609_Orchestrator_Runtime_Core.md`

If WP-0601 through WP-0609 have already been implemented, inspect the actual code and integrate with it. Do not duplicate event, intake, decision, provider, health, assignment, scheduling, or orchestrator models.

## Architectural Intent

The Traffic Controller / Operations Manager is the command-and-personnel layer for work movement.

The Orchestrator is mechanical. It evaluates state, creates dispatch records, and updates queues.

The Traffic Controller / Operations Manager decides operational posture:

- what should move next,
- what should wait,
- what should be assigned,
- what needs revision,
- what needs Steward attention,
- what needs Ingrid boundary review,
- what is blocked by capacity,
- what should be cancelled or deferred,
- what should be escalated.

This package creates local operational control artifacts and commands, not a new office and not a hidden autonomous agent.

## Responsibility Separation

Preserve this separation:

- Steward is final authority.
- Traffic Controller / Operations Manager controls operational movement and queue posture.
- Orchestrator mechanically applies eligible movement and creates dispatch state.
- Helen provisions workers.
- Alfred coordinates institutional operations but does not absorb every responsibility.
- Ingrid governs classification and boundary decisions.
- Providers execute, plan, validate, research, or document according to role.
- Audit and Validation prove and record trust.
- Office of the Steward displays state and decision surfaces.

## Scope

Implement:

1. Operations control decision model.
2. Operations queue review model.
3. Priority recommendation model.
4. Assignment recommendation model.
5. Hold/release/cancel/defer/escalate decision artifacts.
6. CLI command to generate an operations review from current Estate runtime artifacts.
7. CLI command to record an operations decision.
8. Office-readable operations summary artifact.
9. Operational event compatibility hook.
10. Tests for models, review generation, decision recording, and CLI behavior.
11. Concise integration documentation.

## Out of Scope

Do not implement:

- provider execution,
- automatic provider dispatch,
- long-running daemon,
- autonomous infinite loop,
- full AI decision-making agent,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new office creation,
- Office UI changes unless an existing simple data surface can be safely updated,
- live network calls,
- browser automation.

This package may make recommendations and record decisions. It must not silently execute work.

## Implementation Targets

Use existing repository conventions. Preferred files:

- `src/estate/core/traffic_controller.py`
- `src/estate/core/operations_manager.py`
- `src/estate/core/operations_control_runtime.py`
- `tests/test_traffic_controller.py`
- `tests/test_operations_manager.py`
- `tests/test_operations_control_runtime.py`
- `docs/integration/traffic_controller_operations_manager.md`

If the repository already has an operations or traffic controller module, extend it rather than creating duplicates.

## Runtime Artifact Locations

Create directories at runtime as needed:

- `runtime/operations/control/reviews/`
- `runtime/operations/control/decisions/`
- `runtime/operations/control/status/latest.json`
- `runtime/operations/control/status/summary.json`
- `runtime/operations/control/status/summary.md`

Do not commit empty runtime directories unless repository convention requires placeholders.

## Operations Review Model

Implement an operations review artifact with these fields:

- `review_id` string, required
- `created_at` ISO timestamp, required
- `created_by` string, default `traffic_controller.operations_manager`
- `classification` string, required
- `source_artifacts` list, default empty
- `pending_intake_count` integer, default 0
- `blocked_intake_count` integer, default 0
- `scheduled_count` integer, default 0
- `dispatch_pending_count` integer, default 0
- `assignment_active_count` integer, default 0
- `assignment_blocked_count` integer, default 0
- `provider_available_count` integer, default 0
- `provider_blocked_count` integer, default 0
- `provider_saturated_count` integer, default 0
- `requires_steward_attention` boolean, default false
- `requires_boundary_review` boolean, default false
- `recommended_actions` list, default empty
- `warnings` list, default empty
- `errors` list, default empty
- `metadata` object, default empty

Allowed classifications:

- `Public`
- `Estate Internal`
- `Restricted`
- `Steward Only`
- `Local Only`

## Recommended Action Model

Recommended actions should include:

- `action_id` string, required
- `action_type` string, required
- `target_type` string, required
- `target_id` string, optional
- `priority` string, default `normal`
- `reason` string, required
- `requires_steward_approval` boolean, default false
- `requires_boundary_review` boolean, default false
- `safe_summary` string, required
- `metadata` object, default empty

Allowed action types:

- `assign`
- `reprioritize`
- `hold`
- `release`
- `defer`
- `cancel`
- `escalate`
- `request_boundary_review`
- `request_revision`
- `request_validation`
- `no_action`

Allowed target types:

- `intake`
- `schedule`
- `dispatch`
- `assignment`
- `provider`
- `work_package`
- `system`

## Operations Decision Model

Implement and validate operations decision artifacts with these fields:

- `decision_id` string, required
- `created_at` ISO timestamp, required
- `decided_by` string, required
- `decision_type` string, required
- `target_type` string, required
- `target_id` string, optional
- `classification` string, required
- `priority` string, default `normal`
- `reason` string, required
- `next_state` string, optional
- `assignment_label` string, optional
- `provider_id` string, optional
- `worker_id` string, optional
- `seat_id` string, optional
- `requires_boundary_review` boolean, default false
- `requires_steward_attention` boolean, default false
- `summary_safe` boolean, default false
- `metadata` object, default empty

Allowed decision types:

- `assign`
- `reprioritize`
- `hold`
- `release`
- `defer`
- `cancel`
- `escalate`
- `request_boundary_review`
- `request_revision`
- `request_validation`

Allowed priorities:

- `low`
- `normal`
- `high`
- `urgent`

## Operational Semantics

- `assign` may create or update assignment intent, but must not provision a new worker.
- `reprioritize` records priority movement for a target.
- `hold` prevents movement until released.
- `release` marks a held item eligible for normal flow.
- `defer` records that work should wait.
- `cancel` records that work should not proceed.
- `escalate` marks the item for Steward or role attention.
- `request_boundary_review` records that Ingrid or Boundary Office review is needed.
- `request_revision` records that the intake/work package needs correction.
- `request_validation` records that proof is needed before promotion.

No operation may silently execute a provider.

## CLI Requirements

Add commands using existing Estate CLI conventions.

Preferred commands:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat operations-review
.\estate.bat operations-decide --decision-type assign --target-type work_package --target-id WP-0609 --assignment-label A2C2 --decided-by Steward --reason "Assign orchestration runtime to C2"
.\estate.bat operations-decisions-list
```

Commands must:

- read existing runtime artifacts where available,
- tolerate missing upstream artifacts with warnings rather than fatal errors,
- write review/decision artifacts,
- update summary artifacts,
- emit or prepare operational events when available,
- print concise human-readable summaries,
- exit non-zero for malformed command input.

If existing CLI routing uses another pattern, follow it and document actual commands.

## Runtime Inputs

When available, operations review should inspect:

- Orchestrator intake status artifacts,
- intake decision artifacts,
- schedule queue artifacts,
- dispatch queue artifacts,
- assignment board artifacts,
- provider catalog artifacts,
- provider health/capacity artifacts,
- operational event status artifacts.

Missing artifacts should produce warnings, not fake success.

## Office-Readable Summary

Generate `runtime/operations/control/status/summary.json` and `summary.md`.

Summary should include:

- current operational posture,
- items requiring attention,
- blocked items,
- provider capacity warnings,
- assignment gaps,
- recommended next actions,
- timestamp,
- source artifacts inspected.

Sensitive summaries must be redacted unless metadata marks `summary_safe: true`.

## Operational Event Compatibility

If WP-0601 exists, emit operations decision events through the operational event feed.

Suggested event types:

- `Checkpoint Reached`
- `Waiting for Approval`
- `Boundary Review Required`
- `Worker Blocked`
- `Result Returned`

If WP-0601 is unavailable, write operations artifacts so a later bridge can emit events without redesign.

## Boundary Behavior

- Traffic Controller decisions must not weaken classification.
- Restricted, Steward Only, and Local Only summaries must be redacted by default.
- Decision artifacts must not contain credentials, tokens, raw prompts, or private source material.
- Boundary review decisions must remain visible as required work, not hidden errors.

## Tests

Add tests covering:

1. Operations review model validates.
2. Operations decision model validates.
3. Unknown classification rejected.
4. Unknown decision type rejected.
5. Unknown action type rejected.
6. Review generation succeeds with no upstream artifacts and reports warnings.
7. Review generation reads available provider health artifact.
8. Review generation reads available assignment board artifact.
9. Decision artifact is written.
10. Summary artifacts are written.
11. Sensitive summaries are redacted by default.
12. A2C assignment label is preserved.
13. CLI operations-review succeeds.
14. CLI operations-decide succeeds for valid decision.
15. CLI operations-decide fails for invalid decision.
16. CLI operations-decisions-list succeeds with no decisions.

Do not require network access.

## Documentation

Create `docs/integration/traffic_controller_operations_manager.md` with:

- purpose,
- distinction between Traffic Controller / Operations Manager and Orchestrator,
- review model,
- decision model,
- runtime artifact paths,
- CLI examples,
- integration with intake, schedule, dispatch, assignments, provider health, and operational events,
- boundary behavior,
- Office consumption notes.

Keep it concise.

## Acceptance Criteria

Complete when:

- operations review model exists,
- operations decision model exists,
- operations-review CLI works,
- operations-decide CLI works,
- decisions are durable artifacts,
- summary artifacts are produced,
- missing upstream artifacts are handled honestly,
- sensitive summaries are redacted by default,
- A2C assignment labels are preserved,
- operational event compatibility exists,
- tests pass,
- documentation exists,
- no provider execution was implemented,
- no new office was created,
- Orchestrator remains mechanical and distinct from Operations Manager.

## Validation

Run targeted tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
python -m pytest tests/test_traffic_controller.py tests/test_operations_manager.py tests/test_operations_control_runtime.py
.\estate.bat audit
```

If repository conventions require different commands, use those and report actual commands.

Produce an implementation summary with:

- files changed,
- tests run,
- audit result,
- operations review artifact paths,
- operations decision artifact paths,
- blocked items,
- recommended follow-up package.

## Do Not Touch

Do not modify:

- archived institutional memory,
- Alfred responsibility definitions,
- Helen responsibility definitions,
- Ingrid responsibility definitions,
- provider execution code,
- scheduler code except read-only compatibility,
- Office UI components unless explicitly safe and minimal.

## Expected Follow-On Packages

Do not implement these now:

- WP-0611 Office Traffic Controller panel.
- WP-0612 Orchestrator policy rules and priority management.
- WP-0613 Execution Provider Adapter Contract.
