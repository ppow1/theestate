# WP-0503 - Governed Dispatch-to-Adapter Handoff Runtime

Status: Proposed
Priority: High
Owner: Chief Architect #5
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Traffic Controller / Operations Manager, Execution Dispatch Queue, Execution Provider Adapter Contract, Codex Bridge, Office of the Steward, Audit / Validation
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is bounded repository implementation work connecting existing dispatch records to the existing provider-neutral adapter contract. It should not require live provider execution, local GPU access, Codex CLI capacity, or network-dependent tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation and deterministic validation should be possible from repository context. Final local validation may exercise the CLI and runtime artifact writers without calling a provider.
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

Do not bypass Traffic Controller authorization, Dispatch integrity, or the Execution Provider Adapter Contract.

Write deterministic tests and validation evidence so local validation can confirm the result.
```

## Mission

Implement the missing governed handoff layer between an authorized Execution Dispatch Queue item and the existing Execution Provider Adapter Contract.

The Estate already has a provider-agnostic Dispatch Queue and a provider-neutral adapter contract. The current gap is a coherent runtime that takes a dispatch item that is explicitly ready and authorized, translates it into an adapter request, validates the request, writes durable handoff artifacts, updates the dispatch record with the handoff reference, and records lifecycle evidence without calling a live provider.

This package should produce a real implementation capability rather than additional governance.

## Background

The existing execution-provider chain includes:

```text
Provider Routing Recommendations
Execution Dispatch Queue
Execution Provider Adapter Contract
Codex Bridge
Execution Activity Surface
Office provider-routing visibility
```

The Dispatch Queue already stores candidate work and can prepare a Codex Bridge-specific dry-run handoff.

The Execution Provider Adapter Contract already defines:

```text
ExecutionProviderAdapterRequest
ExecutionProviderAdapterResult
ExecutionProviderAdapter
DeterministicDryRunExecutionProviderAdapter
```

It also supports construction from a dispatch record through:

```text
ExecutionProviderAdapterRequest.from_dispatch_record(...)
```

What is missing is a provider-neutral operational bridge that coordinates the existing pieces.

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
docs/integration/execution_provider_adapter_contract.md
docs/integration/provider_routing_recommendations.md
src/estate/core/execution_dispatch.py
src/estate/core/execution_provider_adapter.py
src/estate/core/execution_provider_adapter_runtime.py
src/estate/core/codex_bridge.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
tests/test_execution_dispatch.py
tests/test_execution_provider_adapter.py
tests/test_execution_provider_adapter_runtime.py
```

If any file is missing locally, record it and continue with available canonical files.

## Scope

This package must implement:

1. A provider-neutral handoff runtime that loads an existing dispatch item.
2. Readiness checks that require the dispatch item to be in an explicitly handoff-eligible state.
3. A requirement for an existing movement/authorization reference before preparing handoff.
4. Translation from the dispatch item into `ExecutionProviderAdapterRequest` using the existing adapter contract.
5. Deterministic adapter-request validation before any handoff artifact is accepted.
6. Durable request, result/status, and report artifacts using existing adapter-runtime conventions.
7. Update of the existing dispatch item with the adapter handoff reference.
8. Dispatch lifecycle evidence showing that a handoff was prepared, validated, blocked, or accepted for provider submission.
9. A deterministic dry-run path using `DeterministicDryRunExecutionProviderAdapter`.
10. A CLI surface for preparing, inspecting, validating, and dry-running a dispatch-to-adapter handoff.
11. Focused deterministic tests.
12. Integration documentation.
13. A work-package validation recipe and completion receipt.

## Out Of Scope

This package must not:

- call a live execution provider;
- submit work to Codex Cloud/Web;
- invoke Codex CLI;
- invoke ChatGPT CLI;
- invoke Ollama;
- call network services;
- schedule work;
- select a provider autonomously;
- assign workers;
- authorize movement;
- bypass Traffic Controller constraints;
- create a second Dispatch Queue;
- create a second provider registry;
- create a second event feed;
- create a new office;
- modify Background Operations ownership;
- modify Orchestrator authority;
- mark institutional acceptance;
- automatically transition a dispatch item to Running or Completed merely because a handoff artifact exists.

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
Operations conducts movement.
Traffic Controller authorizes movement according to governance.
```

```text
Recommendations are evidence, not decisions.
Validation results are evidence, not institutional acceptance.
Dispatch remains the governed implementation path.
```

Package-specific boundary note:

```text
Preparing and validating an adapter handoff is not provider execution.
A handoff artifact is not authorization.
A handoff artifact is not institutional acceptance.
```

## Handoff Eligibility Requirements

The runtime must reject or block handoff preparation unless all required conditions are met.

At minimum, require:

```text
dispatch item exists
dispatch state is Ready or another explicitly documented handoff-eligible state
provider is present
classification is present
prompt/work-package source is present
read scope is present when required
write scope is present for workspace-write operations
authorization or decision reference is present
provider is not forbidden
provider is compatible with allowed providers when restrictions exist
```

Do not infer authorization from the absence of a blocker.

## Expected Artifacts

Create a focused runtime module, preferably:

```text
src/estate/core/execution_adapter_handoff_runtime.py
```

Use existing modules instead if repository conventions strongly indicate a cleaner placement, but do not overload unrelated files.

Create focused tests, preferably:

```text
tests/test_execution_adapter_handoff_runtime.py
```

Create integration documentation:

```text
docs/integration/execution_dispatch_to_adapter_handoff.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0503_codex_done.json
```

Add a deterministic validation recipe for:

```text
WP-0503
```

Likely integration touchpoints:

```text
src/estate/cli/main.py
src/estate/core/execution_dispatch.py
src/estate/core/execution_provider_adapter.py
src/estate/core/execution_provider_adapter_runtime.py
src/estate/core/work_package_validation.py
```

Modify only what is necessary.

## Runtime Artifacts

Prefer existing adapter runtime paths and conventions.

Expected artifacts may include:

```text
runtime/execution_adapters/requests/<adapter_request_id>.json
runtime/execution_adapters/results/<adapter_request_id>.json
runtime/execution_adapters/status/latest.json
runtime/execution_adapters/reports/<adapter_request_id>.md
```

If a handoff-specific status artifact is needed, keep it under the existing execution-adapter runtime tree rather than creating a parallel top-level subsystem.

Do not commit live runtime outputs unless explicitly required as evidence.

## CLI Surface

Add a minimal CLI surface consistent with existing patterns, such as:

```text
python -m estate.cli.main execution-adapter-handoff prepare --dispatch-id <id> --json
python -m estate.cli.main execution-adapter-handoff inspect --dispatch-id <id> --json
python -m estate.cli.main execution-adapter-handoff validate --dispatch-id <id> --json
python -m estate.cli.main execution-adapter-handoff dry-run --dispatch-id <id> --json
```

Exact command names may be adjusted to repository conventions.

The CLI must not perform live provider calls.

## State and Evidence Requirements

The runtime should distinguish at least:

```text
not_ready
blocked
authorized_for_handoff
handoff_prepared
handoff_validated
dry_run_completed
accepted_for_provider_submission
```

These are handoff/lifecycle evidence states, not institutional acceptance states.

Do not automatically set the Dispatch Queue item to Running or Completed.

Any dispatch-state mutation must be explicit, minimal, documented, and consistent with existing queue semantics.

## Test Requirements

Tests must cover:

- successful translation from an authorized Ready dispatch item to adapter request;
- rejection when dispatch item is missing;
- rejection when state is not handoff-eligible;
- rejection when authorization/decision reference is missing;
- rejection when provider is forbidden or outside allowed providers;
- rejection when required scope data is missing;
- deterministic dry-run with `live_provider_called: false`;
- dispatch handoff reference update;
- request and result artifact creation;
- no automatic transition to Running or Completed;
- no live provider/network/GPU calls;
- no duplicate queue, provider registry, or event system.

## Validation Rings

### Ring 0 - Static / Structural Validation

Verify required module, tests, documentation, completion receipt, and validation recipe exist.

### Ring 1 - Deterministic Test Validation

Likely commands:

```text
python -m py_compile src/estate/core/execution_adapter_handoff_runtime.py
pytest -q tests/test_execution_adapter_handoff_runtime.py tests/test_execution_provider_adapter.py tests/test_execution_provider_adapter_runtime.py
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0503 --json
```

Exercise the CLI with temporary deterministic dispatch data and confirm no live provider call occurred.

### Ring 2 - Local GPU Reasoning Review

After merge, local Ring 2 review should inspect:

- WP-0503;
- changed files;
- deterministic test results;
- validation report;
- completion receipt;
- sample dispatch and adapter artifacts;
- movement authorization boundary;
- provider-execution boundary;
- Dispatch integrity;
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
handoff_states_implemented
handoff_eligibility_requirements
live_provider_calls_made
dispatch_behavior_modified
provider_adapter_behavior_modified
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

1. An authorized Ready dispatch item can be translated into a valid provider-neutral adapter request.
2. Unauthorized or incomplete items are deterministically blocked.
3. Adapter request and dry-run result artifacts are written using existing runtime conventions.
4. The dispatch item records the handoff reference.
5. No live provider call is performed.
6. No provider is selected autonomously.
7. No worker is assigned automatically.
8. No movement is authorized by this runtime.
9. No dispatch item is automatically marked Running or Completed.
10. Existing Dispatch Queue and Adapter Contract remain the canonical systems.
11. Focused tests pass.
12. WP-0503 validation passes.
13. Completion receipt exists and is ready for Chief Architect review.
14. No new office, registry, queue, event system, or command surface beyond the minimal CLI integration is created.

## Steward / Chief Architect Note

This is a CA5 500-series implementation package.

WP-0501 validated the execution-provider boundary.
WP-0502 recorded the institutional doctrine.
WP-0503 returns CA5 directly to implementation by connecting authorized Dispatch work to the existing provider adapter seam.

The goal is operational progress: a governed, provider-neutral handoff that is real enough to use and safe enough to validate before live provider adapters are introduced.
