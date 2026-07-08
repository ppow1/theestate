# WP-0601 - Operational Event Feed and Office Status

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement a shared Estate operational event feed and Office-readable status surface for workers and providers.

The Estate is moving toward many concurrent workers and multiple provider classes. The Steward must not be required to inspect terminals, browser tabs, or chat scrollback to understand what is active, blocked, completed, or awaiting attention.

This package creates the first common event/status layer that planning providers, execution providers, validation workers, documentation workers, and future Orchestrator components can emit into.

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
- `docs/architecture/execution_provider_operational_visibility_requirements.md`
- `docs/architecture/planning_pipeline.md`
- `docs/architecture/chatgpt_vs_codex.md`
- `collaboration/work_packages/pending/WP-0600_Planning_Provider_Framework.md`

## Architectural Intent

Create the shared operational visibility substrate, not a new office.

The architecture must support this line:

`governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state`

This package should create reusable code and runtime artifacts so the Office of the Steward can answer:

- What is running?
- What is blocked?
- What completed recently?
- What needs Steward attention?
- Which worker or provider produced the activity?
- What work package or assignment is involved?
- What is the validation state?

## Scope

Implement:

1. Common operational event model.
2. Common activity/status model.
3. Event append/write helpers.
4. Status update helpers.
5. Runtime artifact locations for event logs and latest state.
6. CLI command to record a test event.
7. CLI command to summarize active/recent activity.
8. Office-readable JSON status file.
9. Optional Markdown summary file for humans.
10. Tests for event creation, status updates, filtering, and summary generation.
11. Concise integration documentation.

## Out of Scope

Do not implement:

- full Orchestrator,
- scheduler,
- provider execution engine,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new office,
- live Office UI redesign,
- live network integrations,
- provider-specific adapters.

This package may create Office-consumable files, but should not require React/UI work unless the existing Office already has a simple status ingestion point that can be updated safely.

## Implementation Targets

Use existing repository conventions. Preferred files:

- `src/estate/core/operational_events.py`
- `src/estate/core/operational_status.py`
- `tests/test_operational_events.py`
- `tests/test_operational_status.py`
- `docs/integration/operational_event_feed.md`

If existing names or directories already cover this responsibility, extend those instead of creating duplicates.

## Runtime Artifact Locations

Create runtime directories at runtime as needed:

- `runtime/operations/events/`
- `runtime/operations/status/`
- `runtime/operations/status/latest.json`
- `runtime/operations/status/active.json`
- `runtime/operations/status/recent.json`
- `runtime/operations/status/summary.md`

Do not commit empty runtime directories unless repository convention requires placeholder files.

## Event Model

Implement an operational event envelope with these fields:

- `event_id` string, required
- `event_type` string, required
- `state` string, required
- `created_at` ISO timestamp, required
- `updated_at` ISO timestamp, optional
- `worker_id` string, optional
- `worker_role` string, optional
- `provider_id` string, optional
- `provider_type` string, optional
- `assignment_id` string, optional
- `work_package_id` string, optional
- `request_id` string, optional
- `classification` string, required
- `budget_source` string, optional
- `validation_status` string, default `not_validated`
- `requires_attention` boolean, default false
- `message` string, required
- `artifact_paths` list, default empty
- `metadata` object, default empty

Allowed classifications:

- `Public`
- `Estate Internal`
- `Restricted`
- `Steward Only`
- `Local Only`

Allowed states:

- `Planning`
- `Waiting`
- `Running`
- `Reviewing`
- `Blocked`
- `Awaiting Approval`
- `Validation`
- `Completed`
- `Failed`
- `Cancelled`
- `Deferred`

Initial event types:

- `Job Accepted`
- `Planning Started`
- `Execution Started`
- `Checkpoint Reached`
- `Waiting for Approval`
- `Boundary Review Required`
- `Validation Started`
- `Validation Passed`
- `Validation Failed`
- `Commit Created`
- `Result Returned`
- `Execution Complete`
- `Planning Complete`
- `Worker Blocked`
- `Worker Failed`
- `Worker Cancelled`

Unknown event types should fail unless explicitly passed through an extension mechanism. If an extension mechanism is implemented, unknown events must still preserve required fields.

## Activity Status Model

Implement a derived status object suitable for Office display.

Required fields:

- `activity_id`
- `current_state`
- `last_event_type`
- `last_message`
- `started_at`
- `updated_at`
- `elapsed_seconds`
- `worker_id`
- `worker_role`
- `provider_id`
- `provider_type`
- `assignment_id`
- `work_package_id`
- `request_id`
- `classification`
- `budget_source`
- `validation_status`
- `requires_attention`
- `artifact_paths`

Activity identity should be derived from the best available stable field in this order:

1. `request_id`
2. `assignment_id`
3. `work_package_id`
4. `worker_id`
5. generated activity ID

## CLI Requirements

Add commands using existing Estate CLI conventions.

Preferred commands:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat operations-event-record --event <path-to-event-json>
.\estate.bat operations-status-summary
```

The record command must:

1. Load event JSON.
2. Validate fields.
3. Append event artifact.
4. Update derived status files.
5. Print concise summary.
6. Exit non-zero on invalid input.

The summary command must:

1. Read current status artifacts.
2. Print active, blocked, awaiting approval, failed, and recent completed activity.
3. Exit zero even when there is no activity, with a clear message.

If existing CLI routing uses different command names, follow the existing convention and document the actual commands.

## Status Output Requirements

`latest.json` should contain the most recent event and derived status.

`active.json` should contain currently active activities, including states:

- `Planning`
- `Waiting`
- `Running`
- `Reviewing`
- `Blocked`
- `Awaiting Approval`
- `Validation`
- `Deferred`

`recent.json` should contain recent terminal activities, including states:

- `Completed`
- `Failed`
- `Cancelled`

`summary.md` should be concise and human-readable.

## Integration with WP-0600

If WP-0600 has already implemented planning-provider event artifacts, this package should not duplicate them.

Instead, add a bridge/helper so planning-provider lifecycle events can also be represented in the shared operational feed.

If WP-0600 has not yet been implemented, write this package so WP-0600 can call into it later without redesign.

## Boundary Behavior

- Unknown classifications must fail.
- Restricted and Steward Only events may be recorded, but summary output must avoid leaking sensitive metadata.
- Public or Estate Internal summaries may show normal messages.
- Restricted, Steward Only, and Local Only summaries should prefer generic messages unless metadata explicitly marks `summary_safe: true`.

This is not full Ingrid enforcement, but it must avoid obvious sensitive-content leakage in Office-readable summaries.

## Tests

Add tests covering:

1. Valid event accepted.
2. Invalid classification rejected.
3. Invalid state rejected.
4. Event artifact written.
5. Latest status updated.
6. Active status includes running activity.
7. Recent status includes completed activity.
8. Blocked and awaiting-approval activity requires attention.
9. Summary generation works with no activity.
10. Summary generation redacts sensitive messages unless marked safe.
11. CLI record command succeeds for valid event.
12. CLI record command fails for invalid event.
13. CLI summary command succeeds with and without activity.

Do not require network access.

## Documentation

Create `docs/integration/operational_event_feed.md` with:

- purpose,
- event model,
- status model,
- runtime artifact locations,
- CLI examples,
- boundary summary behavior,
- how planning providers should emit into the feed,
- how execution providers should emit into the feed,
- how the Office of the Steward should consume the status files.

Keep it concise.

## Acceptance Criteria

Complete when:

- common event model exists in code,
- common status model exists in code,
- runtime event artifacts are written,
- Office-readable status files are produced,
- CLI record command works,
- CLI summary command works,
- tests pass,
- documentation exists,
- sensitive summaries are redacted by default,
- no new office was created,
- WP-0600 or future providers can integrate without redesign.

## Validation

Run appropriate tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
python -m pytest tests/test_operational_events.py tests/test_operational_status.py
.\estate.bat audit
```

If repository conventions require different commands, use those and report the actual commands.

Produce an implementation summary with:

- files changed,
- tests run,
- audit result,
- blocked items,
- recommended follow-up work package.

## Do Not Touch

Do not modify:

- archived institutional memory,
- Alfred responsibility definitions,
- Helen responsibility definitions,
- Ingrid responsibility definitions,
- Codex Bridge implementation files except for compatibility integration,
- Office UI components unless there is already a safe, obvious status-ingestion point.

## Expected Follow-On Packages

Do not implement these now:

- WP-0602 Office operational activity panel.
- WP-0603 Orchestrator intake and scheduling skeleton.
- WP-0604 Boundary policy enforcement hooks for operational events.
