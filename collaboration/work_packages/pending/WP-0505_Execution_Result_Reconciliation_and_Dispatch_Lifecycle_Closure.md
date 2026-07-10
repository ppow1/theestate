# WP-0505 - Execution Result Reconciliation and Dispatch Lifecycle Closure

Status: Proposed
Priority: High
Owner: Chief Architect #5
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Traffic Controller / Operations Manager, Execution Dispatch Queue, Execution Provider Adapter Contract, Codex Bridge Adapter, Execution Activity Surface, Audit / Validation, Office of the Steward
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is bounded repository implementation work that closes the loop between provider-adapter results and the existing Dispatch and Activity surfaces. It should not require live provider execution, local GPU access, Codex CLI capacity, or network-dependent tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation and deterministic validation should be possible from repository context. Local validation may use synthetic adapter results and temporary runtime roots.
```

Capacity note:

```text
Use Codex Cloud/Web. Do not use Codex CLI unless repository behavior is ambiguous or local runtime evidence contradicts repository artifacts.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, queues, providers, event systems, or command surfaces unless explicitly required.

Do not perform live provider calls.

Do not equate provider completion with institutional acceptance.

Write deterministic tests and validation evidence so local validation can confirm the result.
```

## Mission

Implement the missing result-reconciliation layer that takes an `ExecutionProviderAdapterResult`, links it back to the originating dispatch item, records the result reference, updates the dispatch lifecycle conservatively, publishes execution activity evidence, and prepares the item for validation or human review.

WP-0503 created the governed dispatch-to-adapter handoff runtime. WP-0504 places the existing Codex Bridge behind the adapter contract. WP-0505 should close the operational loop so execution results return to the Estate coherently instead of remaining isolated provider artifacts.

This package must not treat provider success as institutional acceptance.

## Background

The current execution chain is:

```text
Authorized Dispatch Item
        |
        v
Governed Dispatch-to-Adapter Handoff
        |
        v
Execution Provider Adapter
        |
        v
Concrete Provider Adapter / Codex Bridge
        |
        v
ExecutionProviderAdapterResult
```

The missing step is:

```text
ExecutionProviderAdapterResult
        |
        v
Dispatch lifecycle reconciliation
        |
        +--> Execution Activity evidence
        +--> Validation request / state
        +--> Attention or failure state
        +--> Result and artifact references
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
docs/integration/execution_provider_adapter_contract.md
docs/integration/execution_dispatch_to_adapter_handoff.md
docs/integration/codex_bridge_execution_provider_adapter.md
src/estate/core/execution_dispatch.py
src/estate/core/execution_provider_adapter.py
src/estate/core/execution_provider_adapter_runtime.py
src/estate/core/execution_adapter_handoff_runtime.py
src/estate/core/execution_activity.py
src/estate/core/operator_activity_stream.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
tests/test_execution_dispatch.py
tests/test_execution_provider_adapter.py
tests/test_execution_adapter_handoff_runtime.py
```

If a WP-0504 artifact is not yet present locally, record it and continue using the canonical adapter contract and expected result shape.

## Scope

This package must implement:

1. A result-reconciliation runtime that loads an existing dispatch item and an `ExecutionProviderAdapterResult`.
2. Deterministic identity checks linking adapter request ID, dispatch ID, provider ID, and result artifact.
3. Conservative mapping from adapter result status to dispatch lifecycle state.
4. Recording of result and artifact references on the existing dispatch item.
5. Execution Activity and operator-visible lifecycle evidence using existing surfaces.
6. Validation-state preparation when provider execution completes successfully and validation is required.
7. Attention or blocked-state preparation when results are incomplete, ambiguous, failed, or require human review.
8. Explicit preservation of provider result evidence without granting institutional acceptance.
9. Idempotent reconciliation so replaying the same result does not duplicate state changes or event records.
10. A deterministic CLI surface for inspect, reconcile, and report operations.
11. Focused deterministic tests.
12. Integration documentation.
13. A work-package validation recipe and completion receipt.

## Out Of Scope

This package must not:

- call a live provider;
- invoke Codex CLI, ChatGPT CLI, Ollama, GPU, or network services;
- authorize movement;
- select providers;
- assign workers;
- create a new dispatch queue;
- create a new provider registry;
- create a new event system;
- create a new office;
- replace the Execution Activity Surface;
- replace Audit or Validation;
- automatically mark work institutionally accepted;
- automatically merge, promote, or approve repository changes;
- automatically repair provider output;
- modify Background Operations ownership;
- modify Traffic Controller authority;
- modify Orchestrator authority.

## Architectural Boundaries

This package must preserve:

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.
```

```text
Validation results are evidence, not institutional acceptance.
Dispatch remains the governed implementation path.
```

Package-specific boundary note:

```text
Provider completion closes provider execution, not institutional acceptance.
Successful provider output normally advances to Validation, not directly to Accepted.
```

## Result-to-Dispatch Mapping

Implement a conservative mapping similar to the following, adjusted to existing queue semantics:

```text
adapter status: accepted
    -> dispatch remains Ready or transitions to Running only when explicit execution-start evidence exists

adapter status: completed
    -> dispatch transitions to Validation when validation_required is true
    -> dispatch may transition to Completed only when validation_required is false and explicit completion criteria are met

adapter status: failed
    -> dispatch transitions to Failed
    -> attention_required true

adapter status: blocked
    -> dispatch transitions to Blocked
    -> attention_required true

adapter status: dry_run_completed
    -> dispatch state does not become Running, Validation, or Completed
    -> record dry-run evidence only
```

Do not infer institutional acceptance from any adapter status.

## Reconciliation Requirements

The runtime must reject or block reconciliation when:

- dispatch item does not exist;
- result dispatch ID does not match;
- result adapter request ID does not match the dispatch handoff reference or linked request;
- provider ID does not match the dispatch provider;
- result status is unknown;
- result artifact is malformed;
- reconciliation would regress a terminal state without explicit override authority;
- reconciliation would produce an impossible lifecycle transition.

The runtime must be idempotent for the same result identity and content hash.

## Expected Artifacts

Create a focused runtime module, preferably:

```text
src/estate/core/execution_result_reconciliation_runtime.py
```

Create focused tests, preferably:

```text
tests/test_execution_result_reconciliation_runtime.py
```

Create integration documentation:

```text
docs/integration/execution_result_reconciliation.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0505_codex_done.json
```

Add deterministic validation recipe for:

```text
WP-0505
```

Likely integration touchpoints:

```text
src/estate/core/execution_dispatch.py
src/estate/core/execution_activity.py
src/estate/core/operator_activity_stream.py
src/estate/core/execution_provider_adapter_runtime.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

Modify only what is necessary.

## Runtime Artifacts

Use existing runtime trees where possible.

Expected reconciliation evidence may live under:

```text
runtime/execution_adapters/reconciliation/<dispatch_id>.json
runtime/execution_adapters/reports/<dispatch_id>_reconciliation.md
```

If the existing runtime conventions provide a better location, use them. Do not create a parallel top-level subsystem.

Do not commit live runtime outputs unless explicitly required as evidence.

## CLI Surface

Add a minimal CLI surface consistent with existing patterns, such as:

```text
python -m estate.cli.main execution-result-reconciliation inspect --dispatch-id <id> --json
python -m estate.cli.main execution-result-reconciliation reconcile --dispatch-id <id> --result <path> --json
python -m estate.cli.main execution-result-reconciliation report --dispatch-id <id>
```

Exact command names may be adjusted to repository conventions.

The CLI must not call providers or grant acceptance.

## Activity and Visibility Requirements

Reconciliation should publish evidence through existing surfaces for at least:

```text
provider_result_received
provider_result_blocked
provider_execution_failed
provider_execution_completed
provider_result_ready_for_validation
provider_result_requires_attention
```

Use existing activity/event mechanisms when possible. Do not create a duplicate event feed.

Office-visible summaries should distinguish:

- provider execution state;
- dispatch state;
- validation state;
- attention state;
- institutional acceptance state.

## Test Requirements

Tests must cover:

- successful completed-result reconciliation to Validation;
- completed result with validation not required;
- failed result to Failed with attention required;
- blocked result to Blocked with attention required;
- dry-run result without execution-state advancement;
- mismatched dispatch ID rejection;
- mismatched provider ID rejection;
- malformed result rejection;
- impossible lifecycle transition rejection;
- terminal-state regression protection;
- result and artifact reference persistence;
- activity evidence creation through existing surfaces;
- idempotent replay of the same result;
- no institutional acceptance mutation;
- no live provider, subprocess, network, GPU, Ollama, ChatGPT, or Codex CLI calls.

## Validation Rings

### Ring 0 - Static / Structural Validation

Verify module, tests, documentation, completion receipt, and validation recipe exist.

### Ring 1 - Deterministic Test Validation

Likely commands:

```text
python -m py_compile src/estate/core/execution_result_reconciliation_runtime.py
pytest -q tests/test_execution_result_reconciliation_runtime.py tests/test_execution_dispatch.py tests/test_execution_provider_adapter.py
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0505 --json
```

### Ring 2 - Local GPU Reasoning Review

After merge, local Ring 2 review should inspect:

- WP-0505;
- changed files;
- deterministic test output;
- validation report;
- completion receipt;
- sample dispatch, adapter result, reconciliation, and activity artifacts;
- lifecycle-transition correctness;
- institutional-acceptance boundary;
- duplicate-system risk.

Ring 2 is review evidence, not institutional acceptance.

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
result_status_mappings
lifecycle_transitions_implemented
idempotency_strategy
activity_events_emitted
live_provider_calls_made
dispatch_behavior_modified
provider_adapter_behavior_modified
activity_surface_behavior_modified
background_operations_behavior_modified
orchestrator_behavior_modified
authorization_behavior_modified
institutional_acceptance_behavior_modified
runtime_artifacts_written
known_limitations
ready_for_ca_review
```

The receipt must explicitly state:

```text
live_provider_calls_made: false
authorization_behavior_modified: false
institutional_acceptance_behavior_modified: false
```

## Acceptance Criteria

This package is complete when:

1. Adapter results can be deterministically linked to originating dispatch items.
2. Valid provider results update dispatch lifecycle conservatively.
3. Successful execution normally advances to Validation rather than institutional acceptance.
4. Failed and blocked results create attention-visible states.
5. Dry-run results do not falsely advance execution state.
6. Result and artifact references are persisted.
7. Existing Execution Activity surfaces receive lifecycle evidence.
8. Reconciliation is idempotent.
9. Mismatched or malformed results are blocked.
10. No live provider call occurs.
11. No movement authorization is introduced.
12. No institutional acceptance is introduced.
13. Existing Dispatch, Adapter, Activity, Audit, and Validation systems remain canonical.
14. Focused tests pass.
15. WP-0505 validation passes.
16. Completion receipt exists and is ready for Chief Architect review.

## Steward / Chief Architect Note

This is a CA5 500-series implementation package.

WP-0503 created governed dispatch-to-adapter handoff.
WP-0504 creates the first concrete provider adapter.
WP-0505 closes the result path back into Dispatch, Activity, and Validation without confusing provider completion with institutional acceptance.
