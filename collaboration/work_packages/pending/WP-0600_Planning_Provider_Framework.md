# WP-0600 - Planning Provider Framework

Status: Pending  
Author: Chief Architect #6  
Intended Executor: Codex  
Classification: Estate Internal

## Mission

Implement the first Estate Planning Provider Framework.

This package creates code contracts, request/response models, lifecycle events, provider registration, a local stub provider, a CLI entry point, runtime artifacts, tests, and concise integration documentation.

This is not a live ChatGPT CLI adapter. It is the framework that future ChatGPT, local LLM, and other planning providers will implement.

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
- `docs/architecture/chatgpt_role_in_estate.md`
- `docs/architecture/chatgpt_vs_codex.md`
- `docs/architecture/planning_pipeline.md`
- `docs/architecture/chatgpt_connector_characterization.md`
- `docs/architecture/execution_provider_operational_visibility_requirements.md`
- `docs/security/chatgpt_boundary_policy_draft.md`

## Architectural Intent

Implement a reusable provider framework, not a one-off product integration.

Preserve these boundaries:

- Planning is not implementation.
- Implementation is not validation.
- ChatGPT is not Alfred.
- ChatGPT is not the Orchestrator.
- GitHub is an adapter, not the Communication Bus.
- Terminal output is not enough operational visibility.
- Workers, providers, offices, and runtime state remain separate concepts.

The framework must support this line:

`governed dispatch -> visible activity -> structured events -> auditable result -> Steward-visible decision state`

## Scope

Implement:

1. Planning provider request model.
2. Planning provider response model.
3. Planning provider lifecycle event model.
4. Planning provider interface or abstract base class.
5. Provider registry.
6. Deterministic local stub provider.
7. Runtime artifact writer.
8. CLI command for running a planning provider request from JSON.
9. Event artifacts suitable for future Office of the Steward consumption.
10. Latest status artifact suitable for future Office of the Steward consumption.
11. Tests for the framework.
12. Concise integration documentation.

## Out of Scope

Do not implement:

- live ChatGPT CLI integration,
- live OpenAI API calls,
- Codex Bridge,
- Orchestrator,
- Alfred redesign,
- Helen redesign,
- Ingrid redesign,
- new offices,
- cloud dispatch,
- Office UI changes,
- production scheduler.

Tests must not require network access.

## Implementation Targets

Use existing repository conventions. Preferred files:

- `src/estate/core/planning_provider.py`
- `src/estate/core/planning_provider_registry.py`
- `src/estate/core/planning_provider_events.py`
- `src/estate/core/planning_provider_runtime.py`
- `tests/test_planning_provider.py`
- `tests/test_planning_provider_registry.py`
- `tests/test_planning_provider_runtime.py`
- `docs/integration/planning_provider_framework.md`

Add a CLI command using the existing Estate CLI pattern. Preferred command name:

- `planning-provider-run`

Preferred invocation:

```powershell
Clear-Host
cd A:\theestate
.\estate.bat planning-provider-run --request <path-to-request-json>
```

If the repo uses another command routing pattern, integrate with the existing pattern and document the actual command.

## Request Envelope

Implement and validate a request envelope with these fields:

- `request_id` string, required
- `provider_id` string, required
- `requested_by` string, required
- `worker_id` string, optional
- `mailbox_id` string, optional
- `work_package_id` string, optional
- `classification` string, required
- `planning_intent` string, required
- `prompt` string, required
- `context_paths` list, default empty
- `allowed_output_paths` list, default empty
- `created_at` ISO timestamp, required
- `budget_source` string, optional
- `requires_boundary_review` boolean, default false
- `metadata` object, default empty

Allowed classifications:

- `Public`
- `Estate Internal`
- `Restricted`
- `Steward Only`
- `Local Only`

Reject unknown classifications.

## Response Envelope

Implement and validate a response envelope with these fields:

- `request_id` string, required
- `provider_id` string, required
- `status` string, required
- `started_at` ISO timestamp, required
- `finished_at` ISO timestamp, required
- `summary` string, required
- `output_text` string, optional
- `artifacts` list, default empty
- `events` list, default empty
- `warnings` list, default empty
- `errors` list, default empty
- `classification` string, required
- `requires_review` boolean, default false
- `validation_status` string, default `not_validated`
- `metadata` object, default empty

Allowed statuses:

- `completed`
- `queued`
- `blocked`
- `failed`

Allowed validation statuses:

- `not_validated`
- `validation_required`
- `validation_started`
- `validated`
- `validation_failed`

## Event Envelope

Implement structured lifecycle events with these fields:

- `event_id` string, required
- `request_id` string, required
- `provider_id` string, required
- `worker_id` string, optional
- `event_type` string, required
- `state` string, required
- `message` string, required
- `created_at` ISO timestamp, required
- `classification` string, required
- `metadata` object, default empty

Initial event types:

- `Job Accepted`
- `Planning Started`
- `Checkpoint Reached`
- `Waiting for Approval`
- `Boundary Review Required`
- `Result Returned`
- `Planning Complete`
- `Planning Failed`
- `Validation Required`

Initial states:

- `Planning`
- `Waiting`
- `Running`
- `Reviewing`
- `Blocked`
- `Awaiting Approval`
- `Validation`
- `Completed`
- `Failed`

## Provider Interface

Implement a provider interface with at least:

- `provider_id`
- `display_name`
- `capabilities()`
- `can_handle(request)`
- `run(request)`

Initial capability names:

- `planning`
- `architecture`
- `governance_draft`
- `work_package_draft`
- `documentation_draft`

## Stub Provider

Implement deterministic provider:

- Provider ID: `stub.planning.echo`

Behavior:

- Accepts `Public`, `Estate Internal`, and `Local Only` requests.
- Blocks `Restricted` and `Steward Only` unless request metadata contains `boundary_approved: true`.
- Emits lifecycle events.
- Returns deterministic output including request intent and summary.
- Writes request, result, events, and latest status artifacts.

## Runtime Artifacts

Write artifacts under:

- `runtime/planning_provider/requests/<request_id>.json`
- `runtime/planning_provider/results/<request_id>.json`
- `runtime/planning_provider/events/<request_id>.jsonl`
- `runtime/planning_provider/status/latest.json`

Create runtime directories as needed.

`latest.json` must include at least:

- `request_id`
- `provider_id`
- `worker_id`
- `current_state`
- `status`
- `planning_intent`
- `started_at`
- `updated_at`
- `elapsed_seconds`
- `classification`
- `validation_status`
- `requires_review`
- `summary`

## CLI Requirements

The CLI command must:

1. Load request JSON.
2. Validate required fields.
3. Resolve provider.
4. Run provider.
5. Write runtime artifacts.
6. Print concise summary.
7. Exit non-zero for invalid requests, missing provider, blocked request, or provider failure.

## Boundary Behavior

Implement clear failures for:

- unknown classification,
- missing provider,
- missing prompt,
- missing planning intent.

Implement clear blocked result for:

- `Restricted` without boundary approval,
- `Steward Only` without boundary approval.

Blocked actions must explain why.

Silent failure is unacceptable.

## Tests

Add tests for:

1. Valid request model.
2. Invalid classification rejected.
3. Registry resolves stub provider.
4. Missing provider fails clearly.
5. Stub provider completes allowed request.
6. Stub provider blocks restricted request without approval.
7. Stub provider allows restricted request with approval metadata.
8. Event artifact emitted.
9. Result artifact emitted.
10. Latest status artifact emitted.
11. CLI succeeds for valid request.
12. CLI exits non-zero for blocked request.

Use existing repository test style.

## Documentation

Create `docs/integration/planning_provider_framework.md` with:

- purpose,
- provider model,
- request envelope,
- response envelope,
- event envelope,
- runtime artifact locations,
- CLI example,
- stub provider example,
- boundary behavior,
- future ChatGPT provider notes,
- future Orchestrator notes.

Keep it concise.

## Acceptance Criteria

Complete when:

- contracts exist in code,
- stub provider runs locally without network calls,
- request, response, and event envelopes validate,
- runtime artifacts are written,
- latest status artifact is written,
- boundary-denial behavior works,
- CLI command works,
- tests pass,
- documentation exists,
- no new office was created,
- the framework can support a future ChatGPT provider without redesign.

## Validation

Run appropriate tests and audit. At minimum try:

```powershell
Clear-Host
cd A:\theestate
python -m pytest tests/test_planning_provider.py tests/test_planning_provider_registry.py tests/test_planning_provider_runtime.py
.\estate.bat audit
```

If the repository uses different commands, use existing conventions and report the actual commands.

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
- Codex Bridge implementation files except for import compatibility,
- Office UI components.

## Expected Follow-On Packages

Do not implement these now, but expect later packages:

- WP-0601 ChatGPT planning provider adapter or CLI characterization harness.
- WP-0602 Office planning-provider activity panel.
- WP-0603 Orchestrator intake integration.
- WP-0604 Boundary enforcement hooks for provider requests.
