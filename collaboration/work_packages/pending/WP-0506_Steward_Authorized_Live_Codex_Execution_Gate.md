# WP-0506 - Steward-Authorized Live Codex Execution Gate

Status: Proposed
Priority: High
Owner: Chief Architect #5
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Steward, Traffic Controller / Operations Manager, Execution Dispatch Queue, Governed Dispatch-to-Adapter Handoff Runtime, Codex Bridge Execution Provider Adapter, Audit / Validation, Office of the Steward
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is bounded repository implementation work that adds an explicit local execution gate around the existing Codex Bridge adapter. Codex Cloud/Web can implement the gate, tests, CLI, and documentation without consuming local Codex CLI capacity or making live provider calls.
```

Local runtime required:

```text
partially
```

Local runtime requirement details:

```text
Repository implementation and deterministic tests do not require the local runtime. Final Steward acceptance should include an optional local smoke test against the installed Codex CLI, but the package must remain complete and testable without a live provider call.
```

Capacity note:

```text
Use Codex Cloud/Web for implementation. Do not use Codex CLI during implementation or deterministic validation. Any later live local smoke test must be explicitly initiated by the Steward.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, queues, providers, event systems, or command surfaces unless explicitly required.

Do not perform live provider calls in deterministic tests.

Do not authorize yourself to execute.

Do not bypass Traffic Controller authorization, Dispatch integrity, the governed handoff runtime, or the Execution Provider Adapter Contract.

Write deterministic tests and validation evidence so local validation can confirm the result.
```

## Mission

Implement the first explicitly gated live execution path for the existing Codex Bridge Execution Provider Adapter.

WP-0503 established governed dispatch-to-adapter handoff. WP-0504 placed the Codex Bridge behind the provider adapter contract. WP-0505 is closing provider results back into Dispatch, Activity, and Validation. WP-0506 should make actual local Codex execution possible only when an already-authorized dispatch item, validated adapter request, explicit Steward execution approval, clean workspace, and approved local runtime conditions are all present.

This package must turn live execution from an implicit callable seam into a deliberate, auditable operation.

## Background

The existing concrete Codex Bridge adapter already supports `submit(...)` through an injectable `bridge_runner`. It deliberately refuses submission when no runner is supplied.

The existing Codex Bridge already enforces bounded provider profiles, approval policy, sandbox restrictions, path restrictions, secret redaction, runtime evidence, and dry-run behavior.

What is missing is an Estate-owned execution gate that decides whether the real local runner may be attached and called for a specific already-authorized handoff.

The Institutional Operations Doctrine remains applicable:

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.

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
src/estate/core/execution_dispatch.py
src/estate/core/execution_adapter_handoff_runtime.py
src/estate/core/execution_provider_adapter.py
src/estate/core/codex_bridge_execution_provider_adapter.py
src/estate/core/codex_bridge.py
src/estate/core/execution_provider_adapter_runtime.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
tests/test_execution_adapter_handoff_runtime.py
tests/test_codex_bridge_execution_provider_adapter.py
tests/test_codex_bridge.py
```

If a WP-0505 artifact is not yet present locally, record it and continue using the existing adapter and Dispatch contracts.

## Scope

This package must implement:

1. A live execution authorization record model.
2. A local execution gate that validates an existing dispatch item and adapter request before attaching the real Codex Bridge runner.
3. Explicit Steward approval requirements for live execution.
4. Traffic Controller / movement authorization reference checks.
5. Dispatch state and handoff-reference checks.
6. Clean-workspace checks that block live execution when the active repository is dirty, unless an explicit Steward-approved exception record exists.
7. Provider, profile, sandbox, path-scope, classification, and work-package source checks.
8. Local Codex binary availability checks.
9. A preview command that shows exactly what would execute without calling the provider.
10. An explicit execute command that requires a matching approval record and a deliberate confirmation flag.
11. Durable execution request, approval, decision, result, and audit artifacts under existing execution-adapter or Codex Bridge runtime trees.
12. Accurate recording of `live_provider_called`.
13. Conservative dispatch lifecycle updates through existing functions.
14. A deterministic fake-runner path for tests.
15. Focused deterministic tests.
16. Integration documentation.
17. A work-package validation recipe and completion receipt.

## Out Of Scope

This package must not:

- select a provider autonomously;
- authorize movement;
- create a new dispatch queue;
- create a new provider registry;
- create a new event system;
- create a new office;
- bypass the existing Codex Bridge;
- bypass the existing concrete provider adapter;
- enable danger-full-access;
- enable arbitrary CLI argument passthrough;
- enable Codex Cloud apply;
- automatically stash, commit, reset, clean, or repair the developer workspace;
- execute from an unapproved dirty tree;
- infer approval from the absence of a blocker;
- auto-approve repository changes;
- auto-merge provider output;
- equate provider success with validation or institutional acceptance;
- require live provider calls in tests;
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
The gate verifies authority; it does not create authority.
The confirmation flag expresses operator intent; it is not authorization by itself.
Provider execution is not validation.
Provider success is not institutional acceptance.
```

## Authorization Record Requirements

Create a deterministic authorization record shape containing at least:

```text
execution_authorization_id
dispatch_id
adapter_request_id
provider_id
provider_type
work_package_id
decision_reference
traffic_controller_authorization_reference
steward_approval_reference
approved_by
approved_at
approval_scope
allowed_sandbox
allowed_read_paths
allowed_write_paths
approved_codex_profile
workspace_commit
workspace_clean_required
expires_at
revoked
revoked_at
revocation_reason
metadata
```

The gate must reject expired, revoked, mismatched, incomplete, or overly broad authorization records.

## Live Execution Eligibility

At minimum, require:

```text
dispatch item exists
dispatch state is Ready
dispatch handoff reference exists
adapter request exists and validates
adapter request matches dispatch ID and provider
decision reference exists
Traffic Controller authorization reference exists
Steward approval reference exists
execution authorization record matches the request
execution authorization is not expired or revoked
workspace commit matches the approved commit
workspace is clean when required
Codex binary is available
provider profile is approved
sandbox is read-only or workspace-write
workspace-write paths are explicitly approved
no forbidden path overlaps exist
no danger-full-access or bypass flags are present
explicit execute confirmation flag is present
```

Do not infer authorization from a prior dry run.

## Expected Artifacts

Create a focused gate module, preferably:

```text
src/estate/core/codex_live_execution_gate.py
```

Create focused tests, preferably:

```text
tests/test_codex_live_execution_gate.py
```

Create integration documentation:

```text
docs/integration/steward_authorized_live_codex_execution.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0506_codex_done.json
```

Add deterministic validation recipe for:

```text
WP-0506
```

Likely integration touchpoints:

```text
src/estate/core/codex_bridge_execution_provider_adapter.py
src/estate/core/execution_dispatch.py
src/estate/core/execution_provider_adapter_runtime.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

Modify only what is necessary.

## Runtime Artifacts

Use existing runtime roots where possible.

Expected paths may include:

```text
runtime/execution_adapters/authorizations/<execution_authorization_id>.json
runtime/execution_adapters/executions/<adapter_request_id>.json
runtime/execution_adapters/reports/<adapter_request_id>_live_execution.md
runtime/codex_bridge/<existing bridge evidence paths>
```

Do not create a parallel top-level execution subsystem.

Do not commit live runtime outputs unless explicitly required as evidence.

## CLI Surface

Add a deliberate CLI surface consistent with existing conventions, such as:

```text
python -m estate.cli.main codex-live-execution preview --dispatch-id <id> --authorization <path> --json
python -m estate.cli.main codex-live-execution execute --dispatch-id <id> --authorization <path> --confirm-live-execution --json
python -m estate.cli.main codex-live-execution status --dispatch-id <id> --json
python -m estate.cli.main codex-live-execution report --dispatch-id <id>
```

Exact names may be adjusted to repository conventions.

The execute command must refuse to run without the explicit confirmation flag.

The preview command must never call the provider.

## Workspace Safety Requirements

The gate must:

- identify the current repository commit;
- verify it matches the authorization record when a commit is specified;
- report dirty-tree state;
- block rather than stash, reset, clean, or repair;
- avoid running from generated validation dirt unless explicitly approved by a valid exception record;
- preserve the developer workspace exactly as found when blocked;
- record the reason for any block.

No normal-use stash workflow may be introduced.

## Execution Requirements

When all checks pass, the gate may:

1. Construct or load the validated adapter request.
2. Instantiate `CodexBridgeExecutionProviderAdapter` with the real existing Codex Bridge runner.
3. Record execution-start evidence.
4. Call `submit(...)` exactly once.
5. Persist the adapter result and Codex Bridge evidence.
6. Record whether the provider was actually called.
7. Move the dispatch item to Running only immediately before the provider call.
8. Leave result reconciliation and post-execution lifecycle closure to WP-0505 mechanisms when available.
9. On pre-call failure, leave the item Ready or Blocked according to existing semantics and record no live provider call.
10. On provider failure, record the result and allow reconciliation to determine the final dispatch state.

## Test Requirements

Tests must cover:

- valid authorization record acceptance;
- missing Steward approval rejection;
- missing Traffic Controller authorization rejection;
- mismatched dispatch ID rejection;
- mismatched adapter request ID rejection;
- expired authorization rejection;
- revoked authorization rejection;
- workspace commit mismatch rejection;
- dirty workspace rejection;
- missing Codex binary rejection;
- unsupported profile rejection;
- prohibited sandbox rejection;
- forbidden path overlap rejection;
- missing explicit confirmation rejection;
- preview performs no provider call;
- fake-runner execute success;
- fake-runner execute failure;
- `live_provider_called` accuracy;
- exactly-once runner invocation;
- no automatic validation, acceptance, merge, stash, reset, clean, or repair behavior;
- no real Codex CLI, network, GPU, Ollama, or ChatGPT calls.

## Validation Rings

### Ring 0 - Static / Structural Validation

Verify module, tests, documentation, completion receipt, and validation recipe exist.

### Ring 1 - Deterministic Test Validation

Likely commands:

```text
python -m py_compile src/estate/core/codex_live_execution_gate.py
pytest -q tests/test_codex_live_execution_gate.py tests/test_codex_bridge_execution_provider_adapter.py tests/test_codex_bridge.py
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0506 --json
```

All submit tests must use an injected fake runner.

### Ring 2 - Steward-Local Review and Optional Smoke Test

Ring 2 should first perform a no-live-call reasoning review over:

- WP-0506;
- changed files;
- validation evidence;
- completion receipt;
- sample approval and blocked execution artifacts;
- workspace safety behavior;
- authority references;
- exactly-once execution behavior;
- provider-call evidence.

An optional live local smoke test may occur only after the deterministic review passes and the Steward explicitly approves a bounded test request.

The live smoke test is not required for Codex package completion.

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
authorization_fields_implemented
eligibility_checks_implemented
workspace_safety_checks
live_provider_calls_made_during_implementation
fake_runner_used_for_tests
preview_live_provider_called
execute_confirmation_required
dispatch_behavior_modified
provider_adapter_behavior_modified
codex_bridge_behavior_modified
background_operations_behavior_modified
orchestrator_behavior_modified
authorization_authority_modified
institutional_acceptance_behavior_modified
runtime_artifacts_written
known_limitations
optional_local_smoke_test_required
ready_for_ca_review
```

The receipt must explicitly state:

```text
live_provider_calls_made_during_implementation: false
fake_runner_used_for_tests: true
preview_live_provider_called: false
execute_confirmation_required: true
authorization_authority_modified: false
institutional_acceptance_behavior_modified: false
optional_local_smoke_test_required: false
```

## Acceptance Criteria

This package is complete when:

1. A real local Codex runner can only be attached through the explicit execution gate.
2. Live execution requires matching Dispatch, adapter, Traffic Controller, and Steward authorization evidence.
3. Live execution requires an explicit confirmation flag.
4. Dirty or mismatched workspaces are blocked without automatic repair.
5. Preview performs no provider call.
6. Deterministic tests use a fake runner.
7. Exactly one provider call occurs for an approved execute operation.
8. No provider is selected autonomously.
9. No movement authority is created.
10. No validation, acceptance, merge, stash, reset, clean, or repair authority is introduced.
11. Existing Dispatch, handoff runtime, adapter contract, Codex Bridge adapter, Codex Bridge, result reconciliation, Audit, and Validation remain canonical.
12. Focused tests pass.
13. WP-0506 validation passes.
14. Completion receipt exists and is ready for Chief Architect review.
15. No new office, registry, queue, provider, event system, or competing execution path is created.

## Steward / Chief Architect Note

This is a CA5 500-series implementation package.

WP-0503 prepared governed handoffs.
WP-0504 created the first concrete adapter.
WP-0505 closes results back into Dispatch and Validation.
WP-0506 makes the first real local provider execution possible through explicit Steward approval and auditable safety checks.

This package is the transition from deterministic execution architecture to deliberately authorized live execution.
