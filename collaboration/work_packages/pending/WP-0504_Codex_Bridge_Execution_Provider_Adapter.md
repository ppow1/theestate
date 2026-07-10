# WP-0504 - Codex Bridge Execution Provider Adapter

Status: Proposed
Priority: High
Owner: Chief Architect #5
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Traffic Controller / Operations Manager, Execution Dispatch Queue, Execution Provider Adapter Contract, Codex Bridge, Audit / Validation, Office of the Steward
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is bounded repository implementation work that places the existing Codex Bridge behind the existing Execution Provider Adapter Contract. It should not require live Codex CLI execution, local GPU access, or network-dependent tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation and deterministic validation should be possible from repository context. A later Steward-local smoke test may exercise the real Codex CLI adapter, but live provider execution is not required for baseline completion.
```

Capacity note:

```text
Use Codex Cloud/Web. Do not use Codex CLI for implementation unless repository behavior is ambiguous or local runtime evidence contradicts repository artifacts.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, queues, providers, event systems, or command surfaces unless explicitly required.

Do not perform live provider calls in deterministic tests.

Do not bypass Traffic Controller authorization, Dispatch integrity, the governed handoff runtime, or the Execution Provider Adapter Contract.

Write deterministic tests and validation evidence so local validation can confirm the result.
```

## Mission

Implement the first concrete execution-provider adapter behind the existing Execution Provider Adapter Contract by wrapping the existing Codex Bridge.

WP-0503 established the governed dispatch-to-adapter handoff runtime. WP-0504 should complete the next implementation step: accept an authorized, validated `ExecutionProviderAdapterRequest`, translate it into the existing `CodexBridgeRequest`, invoke the Codex Bridge through an injectable execution seam, and translate the bridge result back into `ExecutionProviderAdapterResult`.

Deterministic tests must use a fake or injected bridge runner. No live Codex CLI execution is required for package completion.

## Background

The Estate now has:

```text
Execution Dispatch Queue
Governed Dispatch-to-Adapter Handoff Runtime
Execution Provider Adapter Contract
Codex Bridge
```

The current gap is that the Codex Bridge is not yet implemented as a concrete `ExecutionProviderAdapter`.

The existing Codex Bridge is a bounded local `codex exec` implementation with sandbox, path, classification, profile, approval, output parsing, event, audit, and secret-redaction behavior.

The existing adapter contract defines:

```text
ExecutionProviderAdapterRequest
ExecutionProviderAdapterResult
ExecutionProviderAdapter
DeterministicDryRunExecutionProviderAdapter
```

This package must connect those existing mechanisms rather than creating a parallel provider path.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/Institutional_Operations_Doctrine.md
docs/integration/execution_provider_adapter_contract.md
docs/integration/execution_dispatch_to_adapter_handoff.md
src/estate/core/execution_provider_adapter.py
src/estate/core/execution_provider_adapter_runtime.py
src/estate/core/execution_adapter_handoff_runtime.py
src/estate/core/execution_dispatch.py
src/estate/core/codex_bridge.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
tests/test_execution_provider_adapter.py
tests/test_execution_provider_adapter_runtime.py
tests/test_execution_adapter_handoff_runtime.py
tests/test_codex_bridge.py
```

If any file is missing locally, record it and continue with available canonical files.

## Scope

This package must implement:

1. A concrete `ExecutionProviderAdapter` implementation for the existing Codex Bridge.
2. Support for the existing Codex provider identities and profiles without creating a new provider registry.
3. Translation from `ExecutionProviderAdapterRequest` to `CodexBridgeRequest`.
4. Translation from `CodexBridgeResult` to `ExecutionProviderAdapterResult`.
5. Preservation of request IDs, dispatch IDs, provider IDs, work-package references, classifications, scopes, expected outputs, validation requirements, and decision references.
6. Deterministic request validation before bridge invocation.
7. A deterministic dry-run path that never invokes the Codex binary.
8. An injectable bridge runner or equivalent seam so tests can exercise submit behavior without live provider calls.
9. Explicit blocked behavior for unsupported providers, invalid profiles, prohibited sandbox modes, missing authorization references, or invalid path scopes.
10. Runtime artifact writing through existing execution-adapter conventions.
11. Lifecycle evidence linking adapter request, Codex Bridge request/result, dispatch ID, and result artifacts.
12. A minimal CLI surface if existing CLI conventions support it cleanly.
13. Focused deterministic tests.
14. Integration documentation.
15. A work-package validation recipe and completion receipt.

## Out Of Scope

This package must not:

- create a new provider registry;
- create a new dispatch queue;
- create a new event system;
- create a new office;
- create a second Codex Bridge;
- bypass the existing Codex Bridge validation logic;
- bypass the governed dispatch-to-adapter handoff runtime;
- select a provider autonomously;
- assign workers;
- authorize movement;
- approve institutional truth;
- enable danger-full-access;
- enable Codex Cloud apply;
- enable arbitrary CLI argument passthrough;
- require live Codex CLI, network, GPU, Ollama, or ChatGPT calls in tests;
- modify Background Operations ownership;
- modify Traffic Controller authority;
- automatically mark a dispatch item Completed solely because the bridge returned a result.

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
Dispatch remains the governed implementation path.
```

Package-specific boundary note:

```text
The Codex Bridge adapter implements provider handoff.
It does not authorize movement.
It does not select itself.
It does not accept institutional truth.
```

## Expected Artifacts

Create a focused concrete adapter module, preferably:

```text
src/estate/core/codex_bridge_execution_provider_adapter.py
```

Use an existing provider-adapter module only if repository conventions clearly make that cleaner.

Create focused tests, preferably:

```text
tests/test_codex_bridge_execution_provider_adapter.py
```

Create integration documentation:

```text
docs/integration/codex_bridge_execution_provider_adapter.md
```

Create completion receipt:

```text
collaboration/work_packages/completions/WP-0504_codex_done.json
```

Add deterministic validation recipe for:

```text
WP-0504
```

Likely integration touchpoints:

```text
src/estate/core/execution_provider_adapter.py
src/estate/core/execution_provider_adapter_runtime.py
src/estate/core/execution_adapter_handoff_runtime.py
src/estate/core/codex_bridge.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

Modify only what is necessary.

## Adapter Requirements

The adapter should support at minimum:

```text
provider_id: codex-cli-openai
provider_type: codex-cli
```

Support for `codex-cli-ollama` may be included if it cleanly uses the same existing Codex Bridge semantics and does not introduce new live local-model behavior in tests.

The adapter must:

- validate that the request provider is supported;
- validate that a decision/authorization reference exists;
- preserve read/write/blocked path scopes;
- map sandbox and profile metadata conservatively;
- preserve `approval_policy: never`;
- keep cloud dispatch/apply disabled unless existing approved behavior explicitly says otherwise;
- block danger-full-access;
- redact secrets through existing Codex Bridge behavior;
- record bridge request/result references in adapter result metadata;
- record whether a live provider was called;
- distinguish dry-run from submit behavior.

## Dry-Run Requirements

The dry-run path must:

1. Validate the adapter request.
2. Translate it into a Codex Bridge request shape.
3. Validate the bridge request using existing bridge validation.
4. Write or return deterministic handoff evidence.
5. Record:

```text
live_provider_called: false
```

6. Never invoke `subprocess`, the Codex binary, network services, or a local model.

## Submit Requirements

The submit path must:

1. Require an injectable or explicit bridge execution seam.
2. Refuse unsupported or ambiguous provider requests.
3. Translate the bridge result back into `ExecutionProviderAdapterResult`.
4. Preserve lifecycle events, changed files, tests run, validation status, errors, warnings, and artifact references where available.
5. Record `live_provider_called` accurately.
6. Avoid automatic institutional acceptance.
7. Avoid automatic dispatch completion unless an existing explicit caller performs that state transition separately.

Deterministic tests must use a fake runner and must not call a real Codex process.

## Runtime Artifacts

Use existing execution-adapter runtime paths and conventions:

```text
runtime/execution_adapters/requests/<adapter_request_id>.json
runtime/execution_adapters/results/<adapter_request_id>.json
runtime/execution_adapters/status/latest.json
runtime/execution_adapters/reports/<adapter_request_id>.md
```

Reference existing Codex Bridge runtime artifacts rather than duplicating them.

Do not commit live runtime outputs unless explicitly required as evidence.

## CLI Surface

If clean and low-risk, add commands such as:

```text
python -m estate.cli.main codex-bridge-adapter validate --request <path> --json
python -m estate.cli.main codex-bridge-adapter dry-run --request <path> --json
```

A live submit command is not required for this package. If added, it must be explicitly gated, must not be exercised in deterministic tests, and must preserve all existing authorization and safety boundaries.

## Test Requirements

Tests must cover:

- supported provider detection;
- unsupported provider blocking;
- request-to-Codex-Bridge translation;
- Codex-Bridge-result-to-adapter-result translation;
- authorization/decision reference requirement;
- sandbox and profile validation;
- path-scope preservation;
- blocked path conflicts;
- dry-run with no live provider call;
- fake-runner submit success;
- fake-runner submit failure;
- lifecycle and artifact reference preservation;
- no automatic dispatch completion;
- no live subprocess, network, GPU, Ollama, ChatGPT, or Codex CLI calls.

## Validation Rings

### Ring 0 - Static / Structural Validation

Verify module, tests, documentation, completion receipt, and validation recipe exist.

### Ring 1 - Deterministic Test Validation

Likely commands:

```text
python -m py_compile src/estate/core/codex_bridge_execution_provider_adapter.py
pytest -q tests/test_codex_bridge_execution_provider_adapter.py tests/test_codex_bridge.py tests/test_execution_provider_adapter.py tests/test_execution_adapter_handoff_runtime.py
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0504 --json
```

### Ring 2 - Local GPU Reasoning Review

After merge, local Ring 2 review should inspect:

- WP-0504;
- changed files;
- deterministic test output;
- validation report;
- completion receipt;
- sample adapter and Codex Bridge request/result artifacts;
- provider selection boundary;
- authorization boundary;
- live-provider-call evidence;
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
supported_provider_ids
supported_provider_types
live_provider_calls_made
dry_run_live_provider_called
fake_runner_used_for_submit_tests
dispatch_behavior_modified
provider_adapter_behavior_modified
codex_bridge_behavior_modified
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
dry_run_live_provider_called: false
fake_runner_used_for_submit_tests: true
authorization_behavior_modified: false
institutional_acceptance_behavior_modified: false
```

## Acceptance Criteria

This package is complete when:

1. The existing Codex Bridge is available through a concrete `ExecutionProviderAdapter`.
2. Authorized adapter requests can be translated into Codex Bridge requests.
3. Codex Bridge results can be translated into adapter results.
4. Dry-run behavior performs no live provider call.
5. Submit behavior is tested through an injectable fake runner.
6. Unsupported providers and invalid requests are blocked.
7. Existing Dispatch Queue, handoff runtime, adapter contract, and Codex Bridge remain canonical.
8. No provider is selected autonomously.
9. No movement is authorized by the adapter.
10. No dispatch item is automatically accepted or completed by the adapter.
11. Focused tests pass.
12. WP-0504 validation passes.
13. Completion receipt exists and is ready for Chief Architect review.
14. No new office, registry, queue, event system, or competing provider path is created.

## Steward / Chief Architect Note

This is a CA5 500-series implementation package.

WP-0503 connected authorized Dispatch work to the provider-neutral adapter seam.
WP-0504 places the first concrete provider implementation behind that seam by adapting the existing Codex Bridge.

This is implementation work, not additional governance.
