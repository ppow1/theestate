# WP-0508 - Governed Execution Session Controller

Status: Proposed
Priority: High
Owner: Chief Architect #5
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Traffic Controller / Operations Manager, Execution Dispatch Queue, Dispatch-to-Adapter Handoff Runtime, Live Execution Gate, Execution Attempt Runtime, Result Reconciliation, Audit / Validation, Office of the Steward
Classification: Estate Internal
Created: 2026-07-10

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is bounded repository implementation work that composes existing execution subsystems into one governed, inspectable execution session. It should not require live provider execution, local GPU access, Codex CLI capacity, or network-dependent tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation and deterministic validation should use fake runners, fake process controllers, temporary runtime roots, and synthetic dispatch/authorization/result records. A later Steward-local smoke test may exercise the real local path, but it is not required for package completion.
```

Capacity note:

```text
Use Codex Cloud/Web. Do not use Codex CLI for implementation or deterministic validation.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, queues, providers, event systems, or command surfaces unless explicitly required.

Do not perform live provider calls in deterministic tests.

Do not select providers, authorize movement, grant acceptance, retry automatically, or repair the workspace.

Write deterministic tests and validation evidence so local validation can confirm the result.
```

## Mission

Implement a governed execution session controller that composes the existing CA5 execution infrastructure into one explicit, auditable operation.

The controller must take an already-authorized dispatch item and drive exactly one execution session through the existing handoff, authorization, attempt, provider-adapter, result-reconciliation, activity, and validation seams.

This package must not replace those systems. It must coordinate them.

The objective is to make the execution chain usable as a coherent capability instead of requiring the Steward to manually invoke each low-level command in the correct order.

## Background

The CA5 execution chain now includes or is establishing:

```text
Execution Dispatch Queue
Governed Dispatch-to-Adapter Handoff Runtime
Codex Bridge Execution Provider Adapter
Execution Result Reconciliation
Steward-Authorized Live Codex Execution Gate
Execution Attempt Lease / Cancellation / Recovery
```

The next gap is controlled composition.

Without a session controller, the operator must manually coordinate:

```text
inspect dispatch
validate readiness
prepare adapter handoff
validate authorization
acquire execution lease
preview live execution
start provider call
record attempt state
persist provider result
reconcile result
release lease
publish final session status
```

That manual sequence is error-prone even when each subsystem is individually correct.

The Institutional Operations Doctrine remains applicable:

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.

Dispatch remains the governed implementation path.
Validation results are evidence, not institutional acceptance.
```

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/Institutional_Operations_Doctrine.md
docs/integration/execution_dispatch_to_adapter_handoff.md
docs/integration/codex_bridge_execution_provider_adapter.md
docs/integration/execution_result_reconciliation.md
docs/integration/steward_authorized_live_codex_execution.md
docs/integration/execution_attempt_lease_cancellation_recovery.md
src/estate/core/execution_dispatch.py
src/estate/core/execution_adapter_handoff_runtime.py
src/estate/core/codex_bridge_execution_provider_adapter.py
src/estate/core/codex_live_execution_gate.py
src/estate/core/execution_attempt_runtime.py
src/estate/core/execution_result_reconciliation_runtime.py
src/estate/core/execution_activity.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

If WP-0507 artifacts are not yet present locally, record that and implement against the expected attempt-runtime contract without inventing a competing lease or cancellation system.

## Scope

This package must implement:

1. A stable execution-session record model.
2. A controller for one already-authorized dispatch item and one execution attempt.
3. Explicit session stages and stage transitions.
4. Session preview that performs no live provider call.
5. Session start that requires existing authorization evidence and explicit confirmation.
6. Composition of the existing dispatch-to-adapter handoff runtime.
7. Composition of the existing live execution gate.
8. Composition of the existing execution-attempt lease/runtime.
9. Composition of the existing concrete provider adapter.
10. Composition of the existing result-reconciliation runtime.
11. Durable stage, status, event-reference, result-reference, and failure evidence.
12. Idempotent resume/inspect behavior after interruption.
13. Explicit stop points for blocked, cancellation-requested, provider-failed, reconciliation-failed, and validation-ready outcomes.
14. No automatic retry.
15. A minimal CLI for preview, start, resume, status, and report.
16. Office-readable session summary through existing activity/status surfaces where practical.
17. Focused deterministic tests.
18. Integration documentation.
19. A work-package validation recipe and completion receipt.

## Out Of Scope

This package must not:

- create a new dispatch queue;
- create a new provider registry;
- create a new event system;
- create a new office;
- create a second execution-attempt system;
- create a second reconciliation system;
- create a second live-execution gate;
- select a provider autonomously;
- authorize movement;
- assign workers;
- automatically retry execution;
- automatically repair, stash, reset, clean, commit, merge, or promote repository changes;
- bypass Traffic Controller or Steward authorization;
- bypass Dispatch;
- bypass the adapter contract;
- bypass the live execution gate;
- bypass the execution-attempt lease;
- equate provider success with validation or institutional acceptance;
- perform live provider calls in deterministic tests;
- modify Background Operations ownership;
- modify Traffic Controller authority;
- modify Steward authority.

## Architectural Boundaries

This package must preserve:

```text
Operations conducts movement.
Traffic Controller authorizes movement according to governance.
Execution Providers implement.
Steward governs.
```

Package-specific boundary note:

```text
The session controller coordinates approved mechanics.
It does not choose work, choose a provider, create authority, grant acceptance, or retry on its own.
```

## Execution Session Record

Define a record containing at least:

```text
execution_session_id
dispatch_id
work_package_id
adapter_request_id
execution_authorization_id
execution_attempt_id
provider_id
provider_type
workspace_commit
state
current_stage
stages_completed
started_at
updated_at
finished_at
preview_only
live_provider_called
cancellation_requested
result_reference
reconciliation_reference
validation_reference
attention_required
attention_reason
blocking_reasons
failure_stage
failure_summary
metadata
```

Use explicit session states such as:

```text
prepared
previewed
authorized
lease_acquired
provider_starting
provider_running
provider_result_received
reconciling
validation_ready
blocked
cancellation_requested
cancelled
failed
completed_execution
```

Adjust names to repository conventions if needed, but preserve the distinctions.

## Session Stage Model

At minimum, implement these ordered stages:

```text
1. dispatch_inspection
2. handoff_validation
3. authorization_validation
4. workspace_validation
5. attempt_lease_acquisition
6. provider_execution_preview_or_start
7. provider_result_persistence
8. result_reconciliation
9. lease_release
10. validation_readiness_publication
11. session_report_publication
```

Every stage must record:

```text
stage
started_at
finished_at
status
input_references
output_references
live_provider_called
errors
warnings
```

## Preview Requirements

Preview must:

- inspect the dispatch item;
- validate handoff eligibility;
- validate authorization records;
- validate workspace and provider requirements;
- inspect attempt/lease availability;
- construct the provider request shape;
- report the exact next operations;
- write preview evidence;
- never acquire a live execution lease unless the existing attempt runtime supports a non-owning reservation mode;
- never call the provider;
- record `live_provider_called: false`.

## Start Requirements

Start must require:

```text
matching dispatch item
matching adapter request
matching live execution authorization
Traffic Controller authorization reference
Steward approval reference
explicit confirmation flag
clean and approved workspace
no conflicting active attempt lease
supported concrete provider adapter
```

Start must:

1. Acquire the attempt lease.
2. Record session and attempt start evidence.
3. Call the existing live execution gate exactly once.
4. Persist the provider result.
5. Invoke existing result reconciliation.
6. Release the lease according to attempt-runtime semantics.
7. Publish final session evidence.

The controller must not independently implement provider execution logic.

## Resume Requirements

Resume must be idempotent and stage-aware.

It must:

- load the durable session record;
- determine the last completed stage;
- inspect existing lease, attempt, provider-result, and reconciliation artifacts;
- continue only from a safe stage boundary;
- refuse to rerun a provider call when evidence shows the call may already have occurred;
- surface manual review when provider-call status is ambiguous;
- never infer that a missing result means no provider-side effect occurred;
- preserve prior failures and evidence.

## Failure Handling

The controller must distinguish:

```text
pre-execution block
lease acquisition failure
provider start failure
provider execution failure
provider result persistence failure
reconciliation failure
lease release failure
validation readiness publication failure
ambiguous interrupted execution
```

A failure after the provider call must preserve all evidence and require careful resume/recovery behavior.

Do not automatically retry.

## Expected Artifacts

Create a focused controller module, preferably:

```text
src/estate/core/execution_session_controller.py
```

Create focused tests, preferably:

```text
tests/test_execution_session_controller.py
```

Create integration documentation:

```text
docs/integration/governed_execution_session_controller.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0508_codex_done.json
```

Add deterministic validation recipe for:

```text
WP-0508
```

Likely integration touchpoints:

```text
src/estate/core/execution_adapter_handoff_runtime.py
src/estate/core/codex_live_execution_gate.py
src/estate/core/execution_attempt_runtime.py
src/estate/core/execution_result_reconciliation_runtime.py
src/estate/core/execution_activity.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

Modify only what is necessary.

## Runtime Artifacts

Use the existing execution-adapter runtime tree:

```text
runtime/execution_adapters/sessions/<execution_session_id>.json
runtime/execution_adapters/session_stages/<execution_session_id>.jsonl
runtime/execution_adapters/status/sessions_summary.json
runtime/execution_adapters/reports/<execution_session_id>_session.md
```

Do not create a parallel top-level execution subsystem.

Do not commit live runtime outputs unless explicitly required as evidence.

## CLI Surface

Add a minimal deliberate CLI surface such as:

```text
python -m estate.cli.main execution-session preview --dispatch-id <id> --authorization <path> --json
python -m estate.cli.main execution-session start --dispatch-id <id> --authorization <path> --confirm-live-execution --json
python -m estate.cli.main execution-session resume --session-id <id> --json
python -m estate.cli.main execution-session status --session-id <id> --json
python -m estate.cli.main execution-session report --session-id <id>
```

Exact names may be adjusted to repository conventions.

Preview must never call the provider.
Start must require explicit confirmation.
Resume must not repeat an ambiguous or already-recorded provider call.

## Activity and Office Visibility

Use existing activity/status surfaces to expose at least:

```text
execution_session_prepared
execution_session_previewed
execution_session_started
execution_session_blocked
execution_session_provider_running
execution_session_provider_result_received
execution_session_reconciling
execution_session_validation_ready
execution_session_cancellation_requested
execution_session_failed
execution_session_completed_execution
execution_session_manual_review_required
```

Do not create a duplicate activity feed.

Office-readable summaries should show:

- session ID;
- dispatch ID;
- work package;
- provider;
- current stage;
- attempt ID;
- live-provider-called state;
- cancellation state;
- result/reconciliation/validation references;
- attention requirement;
- blocking or failure reason.

## Test Requirements

Tests must cover:

- successful preview with no provider call;
- successful fake-runner start through all stages;
- missing authorization block;
- dirty workspace block;
- active conflicting lease block;
- exact single provider-call behavior;
- provider failure preservation;
- reconciliation failure preservation;
- lease release failure reporting;
- successful validation-ready outcome;
- resume after pre-execution interruption;
- resume after provider result exists but reconciliation is missing;
- refusal to repeat an ambiguous provider call;
- idempotent repeated status/report operations;
- cancellation-requested stop behavior;
- no automatic retry;
- no institutional acceptance mutation;
- no real provider, process, network, GPU, Ollama, ChatGPT, or Codex CLI calls.

## Validation Rings

### Ring 0 - Static / Structural Validation

Verify module, tests, documentation, completion receipt, and validation recipe exist.

### Ring 1 - Deterministic Test Validation

Likely commands:

```text
python -m py_compile src/estate/core/execution_session_controller.py
pytest -q tests/test_execution_session_controller.py tests/test_execution_attempt_runtime.py tests/test_codex_live_execution_gate.py tests/test_execution_result_reconciliation_runtime.py
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0508 --json
```

All provider and process behavior must use fakes.

### Ring 2 - Local Reasoning Review

After merge, local Ring 2 review should inspect:

- WP-0508;
- changed files;
- deterministic test results;
- validation report;
- completion receipt;
- sample session, stage, attempt, provider-result, reconciliation, and report artifacts;
- exactly-once provider-call protection;
- resume safety;
- authority and acceptance boundaries;
- duplicate-system risk.

## Completion Receipt Requirements

The completion receipt must include:

```text
work_package_id
status
owner
files_reviewed
files_created
files_modified
validation_commands_run
validation_results
session_states_implemented
session_stages_implemented
resume_strategy
provider_call_deduplication_strategy
failure_classifications
live_provider_calls_made
fake_provider_runner_used
fake_process_controller_used
automatic_retry_implemented
dispatch_behavior_modified
handoff_runtime_behavior_modified
live_execution_gate_behavior_modified
execution_attempt_behavior_modified
reconciliation_behavior_modified
activity_surface_behavior_modified
authorization_behavior_modified
institutional_acceptance_behavior_modified
runtime_artifacts_written
known_limitations
ready_for_ca_review
```

The receipt must explicitly state:

```text
live_provider_calls_made: false
fake_provider_runner_used: true
fake_process_controller_used: true
automatic_retry_implemented: false
authorization_behavior_modified: false
institutional_acceptance_behavior_modified: false
```

## Acceptance Criteria

This package is complete when:

1. One authorized dispatch item can be driven through one coherent execution session.
2. Preview performs no provider call.
3. Start composes existing handoff, gate, attempt, adapter, and reconciliation systems.
4. Exactly one provider call occurs in an approved fake-runner start test.
5. Session state and stage evidence are durable and inspectable.
6. Resume continues safely from known stage boundaries.
7. Ambiguous provider-call state never causes an automatic duplicate call.
8. Failures preserve evidence and identify the failed stage.
9. No automatic retry occurs.
10. No provider is selected autonomously.
11. No movement authority or institutional acceptance is introduced.
12. Existing Dispatch, handoff, gate, attempt, adapter, reconciliation, Activity, Audit, and Validation systems remain canonical.
13. Focused tests pass.
14. WP-0508 validation passes.
15. Completion receipt exists and is ready for Chief Architect review.
16. No new office, registry, queue, provider, event system, or competing execution path is created.

## Steward / Chief Architect Note

This is a CA5 500-series implementation package.

WP-0508 turns the individual execution subsystems into one usable, governed execution session without collapsing their boundaries or introducing autonomous behavior.
