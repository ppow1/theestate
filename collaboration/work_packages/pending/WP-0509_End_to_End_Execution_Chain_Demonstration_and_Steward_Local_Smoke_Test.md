# WP-0509 - End-to-End Execution Chain Demonstration and Steward-Local Smoke Test

Status: Proposed
Priority: High
Owner: Chief Architect #5
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Chief Architect, Traffic Controller / Operations Manager, Execution Dispatch Queue, Execution Session Controller, Audit / Validation, Office of the Steward
Classification: Estate Internal
Created: 2026-07-10

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This package requires repository implementation, deterministic end-to-end testing, evidence generation, and a bounded local smoke-test procedure. Codex Cloud/Web should implement the deterministic harness and documentation without consuming local Codex CLI capacity or making live provider calls during implementation.
```

Local runtime required:

```text
partially
```

Local runtime requirement details:

```text
Deterministic package completion must not require live provider execution. Final Steward review may optionally perform one bounded local Codex CLI smoke test using the installed local runtime, a clean workspace, explicit authorization, narrow scopes, and a harmless work item.
```

Capacity note:

```text
Use Codex Cloud/Web for implementation. Do not use Codex CLI during deterministic implementation or validation. Any live local smoke test must be initiated separately and explicitly by the Steward after deterministic validation passes.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, queues, providers, event systems, or command surfaces unless explicitly required.

Do not perform live provider calls during implementation or deterministic validation.

Do not auto-merge, auto-accept, auto-retry, or repair the workspace.

Build the demonstration and the optional smoke-test procedure around the existing execution chain.
```

## Mission

Prove that the CA5 execution-provider architecture functions as one coherent operational chain.

The package must deliver a deterministic end-to-end demonstration that starts with an already-authorized dispatch item and proceeds through governed handoff, execution-session preview and start, execution-attempt leasing, a fake provider call, provider result persistence, result reconciliation, dispatch transition to Validation, activity publication, and final evidence reporting.

The package must also define a separate, bounded Steward-local smoke-test procedure for one real Codex CLI execution. The live smoke test is optional for package completion and must never run automatically.

## Background

The CA5 execution chain now includes:

```text
Execution Dispatch Queue
Governed Dispatch-to-Adapter Handoff Runtime
Codex Bridge Execution Provider Adapter
Execution Result Reconciliation
Steward-Authorized Live Codex Execution Gate
Execution Attempt Lease / Cancellation / Recovery
Governed Execution Session Controller
Execution Activity Surface
```

The individual subsystems have deterministic tests and validation recipes. What remains is integrated proof that the full chain works together without hidden coupling, duplicate authority, or manual stage manipulation.

The target deterministic flow is:

```text
Authorized Dispatch Item
        |
        v
Session Preview
        |
        v
Handoff Validation
        |
        v
Authorization Validation
        |
        v
Execution Lease Acquisition
        |
        v
Exactly One Fake Provider Call
        |
        v
Provider Result Persistence
        |
        v
Result Reconciliation
        |
        v
Dispatch State = Validation
        |
        v
Activity / Report / Evidence Publication
```

The Institutional Operations Doctrine remains applicable:

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.

Validation results are evidence, not institutional acceptance.
Dispatch remains the governed implementation path.
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
docs/integration/governed_execution_session_controller.md
src/estate/core/execution_dispatch.py
src/estate/core/execution_adapter_handoff_runtime.py
src/estate/core/codex_bridge_execution_provider_adapter.py
src/estate/core/codex_live_execution_gate.py
src/estate/core/execution_attempt_runtime.py
src/estate/core/execution_result_reconciliation_runtime.py
src/estate/core/execution_session_controller.py
src/estate/core/execution_activity.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

If any expected artifact is missing, record the gap and continue with available canonical artifacts. Do not recreate missing subsystems inside this package.

## Scope

This package must implement:

1. A deterministic end-to-end execution demonstration harness.
2. Synthetic but contract-valid dispatch, authorization, adapter, attempt, session, and result fixtures.
3. A fake provider runner that records exactly one invocation.
4. A full execution-session preview with no provider call.
5. A full execution-session start with exactly one fake provider call.
6. Provider result persistence through existing adapter/runtime mechanisms.
7. Result reconciliation through the existing reconciliation runtime.
8. Dispatch transition to Validation when validation is required.
9. Activity and status publication through existing surfaces.
10. Evidence that the execution lease is acquired and released correctly.
11. Evidence that no duplicate provider call occurs during resume or replay.
12. Evidence that institutional acceptance is not granted.
13. A single consolidated demonstration report.
14. A machine-readable demonstration result artifact.
15. A CLI command for deterministic demonstration.
16. A bounded, documented Steward-local smoke-test procedure for one real Codex CLI run.
17. A work-package validation recipe and completion receipt.

## Out Of Scope

This package must not:

- create a new execution queue;
- create a new provider registry;
- create a new event system;
- create a new office;
- create a second session controller;
- create a second attempt runtime;
- create a second reconciliation runtime;
- select providers autonomously;
- authorize movement;
- assign workers;
- perform live provider calls during Codex implementation or deterministic validation;
- automatically execute the optional local smoke test;
- automatically retry failed execution;
- automatically merge provider output;
- automatically mark institutional acceptance;
- automatically stash, reset, clean, repair, or commit the workspace;
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
The demonstration proves mechanics.
It does not grant authority.
The smoke-test procedure enables a bounded human-authorized trial.
It does not create autonomous live execution.
```

## Deterministic Demonstration Requirements

The deterministic demonstration must create a temporary isolated Estate root and exercise the existing execution chain.

At minimum, it must:

1. Create a valid Ready dispatch item.
2. Include explicit decision, Traffic Controller authorization, and Steward approval references.
3. Create a valid execution authorization record.
4. Run execution-session preview.
5. Assert preview records `live_provider_called: false`.
6. Run execution-session start using an injected fake provider runner.
7. Assert exactly one provider invocation.
8. Assert an execution attempt lease is acquired and later released.
9. Persist a completed provider result.
10. Reconcile the result.
11. Assert the dispatch item transitions to Validation when validation is required.
12. Assert result, reconciliation, session, attempt, activity, and report references exist.
13. Re-run status, report, and resume-safe inspection operations.
14. Assert no duplicate provider call occurs.
15. Assert institutional acceptance remains not granted.
16. Produce a consolidated pass/fail summary.

The demonstration must use temporary paths and must not modify the active developer runtime state.

## Demonstration Result Model

Create a machine-readable result containing at least:

```text
demonstration_id
work_package_id
dispatch_id
execution_session_id
execution_attempt_id
adapter_request_id
provider_id
preview_status
start_status
provider_call_count
provider_result_status
reconciliation_status
final_dispatch_state
lease_released
activity_evidence_count
institutional_acceptance_state
live_provider_called
fake_provider_runner_used
started_at
finished_at
artifacts
failures
warnings
```

For the deterministic demonstration, require:

```text
provider_call_count: 1
live_provider_called: false
fake_provider_runner_used: true
final_dispatch_state: Validation
institutional_acceptance_state: not_granted
```

## Expected Artifacts

Create a focused demonstration module, preferably:

```text
src/estate/core/execution_chain_demonstration.py
```

Create focused tests, preferably:

```text
tests/test_execution_chain_demonstration.py
```

Create integration documentation:

```text
docs/integration/end_to_end_execution_chain_demonstration.md
```

Create the Steward-local smoke-test procedure:

```text
docs/operations/steward_local_codex_smoke_test.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0509_codex_done.json
```

Add deterministic validation recipe for:

```text
WP-0509
```

Likely integration touchpoints:

```text
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

Modify existing execution modules only if a real integration defect prevents the demonstration. Record any such defect explicitly and keep the repair minimal.

## Runtime and Evidence Artifacts

The deterministic demonstration should write under its isolated temporary root using existing runtime paths.

The consolidated report may use:

```text
runtime/execution_adapters/demonstrations/<demonstration_id>.json
runtime/execution_adapters/reports/<demonstration_id>_end_to_end.md
```

Do not create another top-level runtime subsystem.

Do not commit live runtime outputs unless the package explicitly creates a curated demonstration evidence artifact.

## CLI Surface

Add a command consistent with existing patterns, such as:

```text
python -m estate.cli.main execution-chain demonstrate --json
```

Optional inspection command:

```text
python -m estate.cli.main execution-chain demonstrate-report --demonstration-id <id>
```

The deterministic demonstration command must:

- use an isolated temporary root by default;
- use a fake provider runner;
- never call a live provider;
- return nonzero on any failed assertion;
- print or return all key artifact references.

Do not add a live smoke-test execution command in this package unless it is explicitly gated through the existing WP-0506 live execution controls.

## Steward-Local Smoke-Test Procedure

The procedure must describe one harmless real local Codex CLI trial.

It must require:

```text
clean working tree
known main commit
narrow read/write scopes
harmless dedicated smoke-test work package or file
explicit Traffic Controller authorization reference
explicit Steward approval reference
valid execution authorization record
session preview reviewed first
no danger-full-access
no bypass flags
no automatic merge
no automatic retry
manual review of result and changed files
manual validation after provider completion
```

The smoke test should prefer a harmless target such as creating or updating a dedicated temporary demonstration artifact under an explicitly approved path.

The procedure must include:

1. Preconditions.
2. Commands to inspect status and preview.
3. Approval checkpoint.
4. Exact start command using existing CLI controls.
5. Expected runtime artifacts.
6. Cancellation and recovery commands.
7. Result reconciliation checks.
8. Validation checks.
9. Cleanup guidance.
10. Abort criteria.

The procedure must not be executed automatically by tests or validation recipes.

## Test Requirements

Tests must cover:

- successful deterministic end-to-end demonstration;
- preview no-provider-call behavior;
- exactly one fake provider call;
- lease acquisition and release;
- result persistence;
- reconciliation to Validation;
- activity evidence creation;
- session report creation;
- no duplicate call during repeated status/report/resume inspection;
- blocked demonstration when authorization fixture is invalid;
- failed fake provider result preservation;
- institutional acceptance remains not granted;
- active repository runtime remains untouched;
- no live subprocess, network, GPU, Ollama, ChatGPT, or Codex CLI calls.

## Validation Rings

### Ring 0 - Static / Structural Validation

Verify demonstration module, tests, documentation, smoke-test procedure, completion receipt, and validation recipe exist.

### Ring 1 - Deterministic Test Validation

Likely commands:

```text
python -m py_compile src/estate/core/execution_chain_demonstration.py
pytest -q tests/test_execution_chain_demonstration.py tests/test_execution_session_controller.py tests/test_execution_attempt_runtime.py tests/test_execution_result_reconciliation_runtime.py
PYTHONPATH=src python -m estate.cli.main execution-chain demonstrate --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0509 --json
```

All provider and process behavior must use fakes.

### Ring 2 - Local Reasoning Review

Local Ring 2 review should inspect:

- WP-0509;
- changed files;
- deterministic test results;
- demonstration result artifact;
- consolidated report;
- completion receipt;
- exactly-once provider-call evidence;
- lease lifecycle;
- result reconciliation;
- institutional-acceptance boundary;
- smoke-test procedure safety;
- duplicate-system risk.

### Optional Ring 3 - Steward-Authorized Live Smoke Test

This optional ring may run only after Rings 0-2 pass.

It requires explicit Steward approval and must use the existing live execution gate and execution-session controller.

It must remain a bounded local trial and must not auto-merge or auto-accept output.

Ring 3 is not required for Codex completion or `production_ready` status of the deterministic package.

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
demonstration_flow
demonstration_result
provider_call_count
live_provider_calls_made_during_implementation
fake_provider_runner_used
lease_acquired_and_released
final_dispatch_state
institutional_acceptance_state
active_runtime_modified
smoke_test_procedure_created
smoke_test_executed
automatic_retry_implemented
automatic_merge_implemented
authorization_behavior_modified
institutional_acceptance_behavior_modified
known_limitations
ready_for_ca_review
```

The receipt must explicitly state:

```text
live_provider_calls_made_during_implementation: false
fake_provider_runner_used: true
provider_call_count: 1
lease_acquired_and_released: true
final_dispatch_state: Validation
institutional_acceptance_state: not_granted
active_runtime_modified: false
smoke_test_procedure_created: true
smoke_test_executed: false
automatic_retry_implemented: false
automatic_merge_implemented: false
authorization_behavior_modified: false
institutional_acceptance_behavior_modified: false
```

## Acceptance Criteria

This package is complete when:

1. A deterministic end-to-end demonstration runs successfully in an isolated root.
2. Preview performs no provider call.
3. Start performs exactly one fake provider call.
4. The execution lease is acquired and released.
5. The provider result is persisted and reconciled.
6. The dispatch item reaches Validation when validation is required.
7. Activity and report evidence are produced.
8. Repeated inspection or safe resume does not duplicate the provider call.
9. Institutional acceptance remains not granted.
10. The active developer runtime is not modified by the demonstration.
11. A bounded Steward-local Codex smoke-test procedure exists.
12. The smoke test is not automatically executed.
13. Focused tests pass.
14. WP-0509 validation passes.
15. Completion receipt exists and is ready for Chief Architect review.
16. No new office, registry, queue, provider, event system, or competing execution path is created.

## Steward / Chief Architect Note

This is a CA5 500-series implementation package.

WP-0503 through WP-0508 built the execution chain.
WP-0509 proves that chain works as one coherent system and prepares the first deliberately controlled local provider trial.

This package is the checkpoint between building execution infrastructure and using it operationally.
