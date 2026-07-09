# WP-0613 - Execution Provider Adapter Contract

Status: Proposed  
Priority: High  
Owner: Chief Architect  
Boundary Authority: Ingrid / Privacy and Boundary Office  
Primary Consumers: Orchestrator Runtime Core, Execution Dispatch Queue, Codex Bridge, future execution providers, Office of the Steward  
Classification: Estate Internal  
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository contract work. It should be implemented by Codex Cloud/Web when capacity is available. It does not need Codex CLI, local GPU, live provider calls, or network access in tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation should be possible from repository context. Local deterministic validation is still required after merge.
```

Capacity note:

```text
Avoid Codex CLI capacity. Use local PowerShell/Python for deterministic validation and local RTX 4090/Ollama for Ring 2 reasoning review.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, providers, event systems, or command surfaces unless explicitly required.

Do not perform live provider calls unless explicitly required.

Do not require live cloud, GPU, or network access in tests unless explicitly approved.

Write deterministic tests and validation evidence so local validation can confirm the result.
```

## Mission

Implement the shared contract between Orchestrator dispatch records and concrete execution-provider adapters.

The contract must keep the Orchestrator and dispatch queue provider-neutral. Codex Bridge should become one adapter behind this contract, not something the Orchestrator calls directly.

## Background

The accepted stack is:

```text
Traffic Controller / Operations Manager
  -> Orchestrator Runtime Core
  -> Dispatch Record
  -> Execution Provider Adapter Contract
  -> Provider Adapter
  -> Execution Provider
  -> Audit / Validation
  -> Office Visibility
```

This package implements the missing adapter-contract seam.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/workers/templates/Codex_Work_Package_Template_v1.md
docs/architecture/execution_provider_operational_visibility_requirements.md
docs/architecture/planning_pipeline.md
collaboration/work_packages/pending/WP-0609_Orchestrator_Runtime_Core.md
collaboration/work_packages/pending/WP-0610_Traffic_Controller_Operations_Manager.md
collaboration/work_packages/pending/WP-0612_Operations_Execution_Integration_Audit.md
docs/governance/workers/WP-CODEX-BRIDGE-IMPLEMENTATION.md
docs/governance/workers/WP-EXECUTION-ACTIVITY-SURFACE-001.md
docs/governance/workers/WP-EXECUTION-DISPATCH-QUEUE-001.md
```

If any file is missing locally, record it in the implementation report and continue with available canonical files.

## Scope

This package must implement:

1. Provider-neutral adapter request model.
2. Provider-neutral adapter response model.
3. Adapter status model.
4. Adapter interface or abstract base class.
5. Adapter compatibility checks against dispatch records.
6. Deterministic dry-run adapter for validation.
7. Runtime artifact writer/loader for adapter requests and results.
8. CLI validation command for adapter request validation and dry-run adapter operation.
9. Compatibility documentation for Codex Bridge integration without direct Orchestrator coupling.
10. Deterministic tests.

## Out Of Scope

This package must not:

- call Codex CLI,
- call ChatGPT CLI,
- call Ollama,
- run provider work,
- implement routing recommendations,
- implement scheduling policy,
- modify Orchestrator behavior beyond import-safe compatibility helpers,
- modify Codex Bridge internals except optional import-safe compatibility shims,
- implement Office UI changes,
- create a new provider registry,
- create a new event system,
- create a new office.

## Architectural Boundaries

This package must preserve the following boundaries:

```text
Planning may propose.
Routing may recommend.
Traffic Controller / Operations Manager decides movement.
Future mechanical coordination layers apply approved movement rules.
Dispatch queues hold candidate work.
Execution provider adapters perform provider handoff.
Audit and Validation produce evidence.
Chief Architect / Steward accepts institutional truth.
```

Package-specific boundary notes:

```text
The adapter contract is the seam between dispatch records and provider-specific adapters. It must keep Orchestrator and dispatch code provider-neutral.
```

## Expected Artifacts

Expected implementation artifacts:

```text
src/estate/core/execution_provider_adapter.py
src/estate/core/execution_provider_adapter_runtime.py
tests/test_execution_provider_adapter.py
tests/test_execution_provider_adapter_runtime.py
docs/integration/execution_provider_adapter_contract.md
```

Optional integration touchpoints, if clean and low-risk:

```text
src/estate/cli/main.py
src/estate/core/orchestrator_dispatch.py
src/estate/core/execution_dispatch_queue.py
src/estate/core/codex_bridge.py
```

Do not create duplicate provider catalog, dispatch queue, or event-feed systems.

## Runtime Artifacts

Use local runtime paths:

```text
runtime/execution_adapters/requests/<request_id>.json
runtime/execution_adapters/results/<request_id>.json
runtime/execution_adapters/status/latest.json
runtime/execution_adapters/status/summary.json
```

Do not commit live runtime outputs unless the package explicitly requires an evidence artifact.

## Contract Requirements

Adapter request fields should include:

```text
adapter_request_id
dispatch_id
provider_id
provider_type
profile_label
work_package_id
work_package_path
prompt_source
classification
read_scope_paths
write_scope_paths
blocked_scope_paths
expected_outputs
validation_required
boundary_review_reference
decision_reference
created_at
metadata
```

Adapter result fields should include:

```text
adapter_request_id
dispatch_id
provider_id
status
started_at
finished_at
summary
artifacts
events
validation_status
errors
warnings
metadata
```

Allowed result statuses:

```text
accepted
dry_run_completed
blocked
failed
completed
```

Adapter interface should include:

```text
adapter_id
provider_id
provider_type
supports(request)
validate_request(request)
dry_run(request)
submit(request)
```

The dry-run adapter must not run provider work.

## Test Requirements

Tests must cover:

- valid adapter request accepted,
- invalid classification rejected,
- missing dispatch ID rejected,
- missing provider ID rejected,
- path scope conflict blocked,
- dry-run adapter validates request without provider work,
- dry-run result artifact written,
- latest status artifact written,
- adapter interface does not require Codex-specific fields,
- Codex Bridge compatibility fields can be represented without coupling,
- no live provider/network/GPU calls.

## Validation Rings

### Ring 0 - Static / Structural Validation

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\execution_provider_adapter.py
Test-Path src\estate\core\execution_provider_adapter_runtime.py
Test-Path tests\test_execution_provider_adapter.py
Test-Path tests\test_execution_provider_adapter_runtime.py
Test-Path docs\integration\execution_provider_adapter_contract.md
python -m py_compile src\estate\core\execution_provider_adapter.py
python -m py_compile src\estate\core\execution_provider_adapter_runtime.py
```

### Ring 1 - Deterministic Test Validation

```powershell
Clear-Host
cd A:\theestate
pytest -q tests/test_execution_provider_adapter.py tests/test_execution_provider_adapter_runtime.py
python -m estate.cli.main validate-work-package --id WP-0613 --json
```

Expected evidence:

```text
runtime/validation/work_packages/WP-0613_validation.json
operations/validation/reports/WP-0613_validation.md
collaboration/work_packages/completions/WP-0613_codex_done.json
```

### Ring 2 - Local GPU Reasoning Review

Reviewer questions:

```text
Did the adapter contract keep Orchestrator provider-neutral?
Did it avoid direct Codex coupling?
Did it avoid provider execution?
Did deterministic validation pass?
Did the completion receipt cover changed files, tests, limitations, and skipped live calls?
Were duplicate registries, dispatch queues, event systems, or offices introduced?
Is this ready for Chief Architect review?
```

Expected commands when available:

```powershell
Clear-Host
cd A:\theestate
python -m estate.cli.main local-gpu-validation-review --work-package WP-0613 --json
python -m estate.cli.main local-gpu-validation-review-report --work-package WP-0613
```

Expected evidence:

```text
runtime/validation/reviews/WP-0613_review.json
runtime/validation/reviews/WP-0613_review.md
```

### Ring 3 - CLI Escalation Validation

Use only when Ring 1 and Ring 2 are insufficient. Prefer read-only validation. Do not repair code unless explicitly assigned.

### Ring 4 - Institutional Acceptance

Chief Architect / Steward acceptance must confirm validation evidence, local review recommendation, unresolved concerns, and promotion or repair decision.

## Completion Receipt Requirements

If implemented by Codex or another provider, create:

```text
collaboration/work_packages/completions/WP-0613_codex_done.json
```

The receipt must include work_package_id, provider, files changed, tests run, validation commands run, runtime artifacts generated, docs updated, Office integration status, skipped live-provider calls, known limitations, and follow-up recommendations.

## Promotion Criteria

This package is ready for promotion when Ring 0 passes, Ring 1 passes, Ring 2 recommends Chief Architect review, Ring 3 is not required or completed, completion receipt is present, no blocking boundary issue remains, and Chief Architect / Steward acceptance is recorded.

## Completion Signal

If implemented by Codex, create the completion receipt and include validation ring evidence paths.
