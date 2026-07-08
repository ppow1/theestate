# WP-0608 - Worker Assignment Board Integration

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first Worker Assignment Board integration for the Estate.

The Estate is now developing intake, scheduling, provider catalog, provider health, operational events, and Office visibility. The next missing institutional surface is a clear assignment board that shows which workers are assigned, what they are assigned to, what provider or seat is involved, and what state the assignment is in.

This package creates file-backed assignment records, assignment status artifacts, CLI commands, operational event compatibility, Office-readable summaries, and tests.

This is not worker provisioning and not provider execution.

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
- `collaboration/work_packages/pending/WP-0603_Orchestrator_Intake_Contract.md`
- `collaboration/work_packages/pending/WP-0604_Provider_Registration_and_Capability_Discovery.md`
- `collaboration/work_packages/pending/WP-0606_Orchestrator_Scheduling_Skeleton.md`
- `collaboration/work_packages/pending/WP-0607_Provider_Health_and_Capacity_Reporting.md`

If WP-0601 through WP-0607 have already been implemented, inspect the actual code and integrate with it. Do not duplicate event, provider, intake, schedule, or health models.

## Architectural Intent

The Estate needs visibility into worker assignment as a separate layer from provider capability and scheduling.

Provider catalog answers: what can perform work?

Provider health answers: is it available?

Orchestrator intake answers: what work is requesting entry?

Scheduling answers: what work has been made eligible for future execution?

Assignment answers: who or what is responsible for this specific unit of work right now?

This package implements assignment records and assignment visibility without provisioning workers or executing work.

The package must support:

`governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state`

## Scope

Implement:

1. Worker assignment model.
2. Assignment state model.
3. Assignment runtime writer/loader.
4. CLI command to create assignment record.
5. CLI command to update assignment state.
6. CLI command to list assignments.
7. Office-readable assignment status artifact.
8. Operational event compatibility hook.
9. Provider catalog and provider health compatibility where available.
10. Tests for assignment creation, updates, summaries, and CLI behavior.
11. Concise integration documentation.

## Out of Scope

Do not implement:

- worker provisioning,
- provider execution,
- scheduler loop,
- automatic assignment algorithm,
- Codex invocation,
- ChatGPT invocation,
- Ollama invocation,
- Office UI changes,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new offices.

This package records assignments; it does not create human or AI workers.

## Terminology

Support assignment notation used operationally by the Steward.

Examples:

- `A2C1` means Assigned to Codex Seat 1 / Codex Chrome profile C1.
- `A2C2` means Assigned to Codex Seat 2 / Codex Chrome profile C2.
- `A2C3` means Assigned to Codex Seat 3 / Codex Chrome profile C3.

Do not hardcode the Estate to only three seats. Treat these as assignment labels and metadata that may expand.

## Implementation Targets

Use existing repository conventions. Preferred files:

- `src/estate/core/worker_assignments.py`
- `src/estate/core/worker_assignment_runtime.py`
- `tests/test_worker_assignments.py`
- `tests/test_worker_assignment_runtime.py`
- `docs/integration/worker_assignment_board.md`

If existing collaboration or work package modules already define assignment models, extend them instead of creating duplicates.

## Runtime Artifact Locations

Create directories at runtime as needed:

- `runtime/workers/assignments/records/`
- `runtime/workers/assignments/status/latest.json`
- `runtime/workers/assignments/status/board.json`
- `runtime/workers/assignments/status/summary.md`

Do not commit empty runtime directories unless repository convention requires placeholders.

## Assignment Record Model

Implement and validate assignment records with these fields:

- `assignment_id` string, required
- `created_at` ISO timestamp, required
- `updated_at` ISO timestamp, required
- `assigned_by` string, required
- `assigned_to` string, required
- `assignment_label` string, optional
- `worker_id` string, optional
- `worker_role` string, optional
- `provider_id` string, optional
- `provider_type` string, optional
- `seat_id` string, optional
- `profile_id` string, optional
- `work_package_id` string, optional
- `work_package_path` string, optional
- `intake_id` string, optional
- `schedule_id` string, optional
- `classification` string, required
- `priority` string, default `normal`
- `state` string, required
- `mission` string, required
- `summary` string, required
- `expected_outputs` list, default empty
- `validation_required` boolean, default true
- `requires_attention` boolean, default false
- `blocked_reason` string, optional
- `artifact_paths` list, default empty
- `metadata` object, default empty

Allowed classifications:

- `Public`
- `Estate Internal`
- `Restricted`
- `Steward Only`
- `Local Only`

Allowed priorities:

- `low`
- `normal`
- `high`
- `urgent`

Allowed assignment states:

- `assigned`
- `accepted`
- `running`
- `blocked`
- `awaiting_approval`
- `reviewing`
- `validation`
- `completed`
- `failed`
- `cancelled`
- `deferred`

## Board Status Model

Generate `board.json` with:

- `generated_at`
- `assignment_count`
- `active_count`
- `blocked_count`
- `awaiting_approval_count`
- `completed_count`
- `failed_count`
- `assignments` list

Each board assignment summary should include:

- `assignment_id`
- `assigned_to`
- `assignment_label`
- `worker_id`
- `worker_role`
- `provider_id`
- `provider_type`
- `seat_id`
- `profile_id`
- `work_package_id`
- `work_package_path`
- `state`
- `priority`
- `classification`
- `mission`
- `safe_summary`
- `validation_required`
- `requires_attention`
- `blocked_reason`
- `updated_at`
- `artifact_paths`

Sensitive summaries must be redacted unless metadata marks `summary_safe: true`.

## CLI Requirements

Add commands using existing Estate CLI conventions.

Preferred commands:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat worker-assignment-create --work-package-id WP-0608 --assigned-to A2C2 --assigned-by Steward --mission "Implement worker assignment board"
.\estate.bat worker-assignment-update --assignment-id <id> --state running
.\estate.bat worker-assignment-list
```

Commands must:

- validate input,
- write assignment records,
- update board/latest status artifacts,
- emit or prepare operational events when state changes,
- print concise output,
- exit non-zero for malformed input.

If existing CLI routing uses another pattern, follow it and document actual commands.

## Provider and Health Compatibility

If WP-0604 provider catalog exists, assignment records should validate or enrich provider IDs where possible.

If WP-0607 provider health exists, assignment board summaries should optionally include provider health/capacity context when available.

If those packages do not exist, assignment logic should still work and clearly omit unavailable enrichment.

## Operational Event Compatibility

If WP-0601 exists, emit assignment state changes through the operational event feed.

Suggested mappings:

- `assigned` -> `Job Accepted`
- `running` -> `Execution Started`
- `blocked` -> `Worker Blocked`
- `awaiting_approval` -> `Waiting for Approval`
- `validation` -> `Validation Started`
- `completed` -> `Execution Complete`
- `failed` -> `Worker Failed`
- `cancelled` -> `Worker Cancelled`

If WP-0601 is not available, write assignment artifacts so later event bridging is possible without redesign.

## Boundary Behavior

- Restricted, Steward Only, and Local Only summaries must be redacted by default.
- Assignment records must not contain credentials, tokens, raw private prompts, or private source material.
- Structural fields such as assignment ID, state, provider ID, and work package ID may be shown unless explicitly restricted.

## Tests

Add tests covering:

1. Valid assignment accepted.
2. Missing assignment ID rejected.
3. Unknown state rejected.
4. Unknown classification rejected.
5. Assignment record written.
6. Assignment update changes state.
7. Board status generated.
8. Latest status generated.
9. Sensitive summaries redacted by default.
10. Summary-safe metadata displays summary.
11. A2C1/A2C2/A2C3 labels are preserved as assignment labels.
12. CLI create succeeds.
13. CLI update succeeds.
14. CLI list succeeds with no assignments.
15. CLI list reports active and blocked assignments.

Do not require network access.

## Documentation

Create `docs/integration/worker_assignment_board.md` with:

- purpose,
- assignment model,
- assignment states,
- runtime artifact locations,
- CLI examples,
- A2C1/A2C2/A2C3 terminology,
- provider catalog integration,
- provider health integration,
- operational event integration,
- Office consumption notes,
- boundary behavior.

Keep it concise.

## Acceptance Criteria

Complete when:

- assignment model exists,
- assignment runtime writer/loader exists,
- create/update/list CLI commands work,
- board/latest status artifacts are produced,
- A2C labels are preserved,
- operational event compatibility exists,
- sensitive summaries are redacted by default,
- tests pass,
- documentation exists,
- no worker provisioning or provider execution was implemented,
- no new office was created.

## Validation

Run targeted tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
python -m pytest tests/test_worker_assignments.py tests/test_worker_assignment_runtime.py
.\estate.bat audit
```

If repository conventions require different commands, use those and report actual commands.

Produce an implementation summary with:

- files changed,
- tests run,
- audit result,
- assignment board artifact paths,
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
- Office UI components.

## Expected Follow-On Packages

Do not implement these now:

- WP-0609 Execution dispatch adapter contract.
- WP-0610 Provider-specific health probes.
- WP-0611 Office worker assignment panel.
