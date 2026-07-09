# WP-0614 - Execution Provider Routing Recommendations

Status: Proposed  
Priority: High  
Owner: Chief Architect  
Boundary Authority: Ingrid / Privacy and Boundary Office  
Primary Consumers: Traffic Controller / Operations Manager, Orchestrator Runtime Core, Execution Dispatch Queue, Execution Provider Adapter Contract, Office of the Steward  
Classification: Estate Internal  
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository implementation and contract work. It should not need local Codex CLI, live provider execution, local GPU access, or network access. Codex Cloud/Web is appropriate when capacity is available.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation should be possible from repository context. Local deterministic validation and local GPU reasoning review are required after merge.
```

Capacity note:

```text
Do not use Codex CLI capacity for implementation unless Cloud/Web cannot complete the package. This package exists partly to prevent accidental premium CLI burn by recommending local deterministic tooling, local RTX 4090/Ollama, Codex Cloud/Web, Codex CLI, ChatGPT planning, or human review based on work characteristics.
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

Implement a provider routing recommendation layer.

This layer recommends provider fit for planned work. It does not schedule work. It does not dispatch work. It does not assign workers. It does not execute providers. It does not choose autonomously. It does not replace the Traffic Controller / Operations Manager, Orchestrator, Execution Dispatch Queue, Execution Provider Adapter Contract, Audit, Validation, or Steward acceptance.

The goal is to produce structured recommendation metadata that helps the Traffic Controller / Operations Manager and future mechanical coordination layers decide whether work is best suited for deterministic local tooling, local RTX 4090/Ollama reasoning, ChatGPT planning, Codex Cloud/Web, Codex CLI, or human review.

## Background

The current execution-provider foundation is now coherent:

```text
Codex Bridge
Execution Activity Surface
Execution Dispatch Queue
Execution Provider Adapter Contract
```

The accepted institutional boundary remains:

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

This package creates recommendations only. It is intentionally not called routing policy.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/workers/templates/Codex_Work_Package_Template_v1.md
docs/architecture/planning_pipeline.md
docs/integration/execution_provider_adapter_contract.md
collaboration/work_packages/pending/WP-0613_Execution_Provider_Adapter_Contract.md
docs/governance/workers/WP-CODEX-BRIDGE-IMPLEMENTATION.md
docs/governance/workers/WP-EXECUTION-ACTIVITY-SURFACE-001.md
docs/governance/workers/WP-EXECUTION-DISPATCH-QUEUE-001.md
```

If any file is missing locally, record it and continue with available canonical files.

## Scope

This package must implement:

1. Provider routing recommendation request model.
2. Provider routing recommendation result model.
3. Deterministic recommendation evaluator.
4. Recommendation rules for provider fit, not policy enforcement.
5. Local RTX 4090/Ollama as a first-class recommendation candidate.
6. Codex Cloud/Web as preferred for broad repository implementation when appropriate.
7. Codex CLI as escalation or local-runtime-required implementation only.
8. Deterministic local tooling as preferred for tests, file checks, schemas, receipts, and validation commands.
9. Human review as required for boundary, authority, classification, or institutional acceptance decisions.
10. Runtime artifact writer/loader for recommendation requests and results.
11. CLI commands to evaluate a recommendation from JSON and explain the recommendation.
12. Deterministic tests and integration documentation.

## Out Of Scope

This package must not:

- implement routing policy,
- schedule work,
- dispatch work,
- assign workers,
- execute providers,
- call Codex CLI,
- call ChatGPT CLI,
- call Ollama,
- call live network services,
- modify Orchestrator runtime behavior,
- modify Execution Dispatch Queue behavior,
- modify Codex Bridge behavior,
- create a new provider catalog,
- create a new dispatch queue,
- create a new event system,
- create a new office.

## Architectural Boundaries

This package must preserve:

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

Package-specific boundary note:

```text
A recommendation is evidence for a decision. It is not the decision.
```

## Expected Artifacts

Expected implementation artifacts:

```text
src/estate/core/provider_routing_recommendations.py
src/estate/core/provider_routing_recommendations_runtime.py
tests/test_provider_routing_recommendations.py
tests/test_provider_routing_recommendations_runtime.py
docs/integration/provider_routing_recommendations.md
```

Optional integration touchpoints, if clean and low-risk:

```text
src/estate/cli/main.py
src/estate/core/provider_catalog.py
src/estate/core/execution_provider_adapter.py
src/estate/core/execution_dispatch_queue.py
```

Do not create duplicate provider catalog, dispatch queue, event feed, or Office surface systems.

## Runtime Artifacts

Use local runtime paths:

```text
runtime/provider_routing/recommendations/<recommendation_id>.json
runtime/provider_routing/status/latest.json
runtime/provider_routing/status/summary.json
runtime/provider_routing/reports/<recommendation_id>.md
```

Do not commit live runtime outputs unless explicitly required as evidence.

## Recommendation Model Requirements

Recommendation request fields should include:

```text
routing_request_id
source_artifact
work_package_id
mission_summary
work_type
requires_repo_write
requires_local_runtime
requires_gpu
requires_network
requires_large_context
requires_human_authority
requires_boundary_review
classification
estimated_complexity
estimated_context_size
expected_artifacts
allowed_paths
blocked_paths
validation_required
metadata
```

Recommendation result fields should include:

```text
routing_request_id
recommendation_id
recommended_provider
alternate_providers
provider_rationale
capacity_note
local_runtime_required
human_review_required
boundary_review_required
validation_rings_required
not_recommended
created_at
metadata
```

Allowed recommended providers:

```text
deterministic_local_tooling
local_ollama_gpu
chatgpt_planning
codex_cloud_web
codex_cli
human_review
```

## Recommendation Rules

Implement deterministic rules similar to:

```text
Use deterministic_local_tooling for file checks, schema checks, pytest, receipts, and static validation.
Use local_ollama_gpu for bounded reasoning review, decomposition review, classification review, and validation evidence review.
Use chatgpt_planning for architectural planning, decomposition, governance prose, and provider-neutral work-package design.
Use codex_cloud_web for broad repository implementation when local runtime is not required.
Use codex_cli only when local runtime context is materially required or when escalation has been approved.
Use human_review when authority, policy, boundary, classification, resident identity, or institutional acceptance is required.
```

The evaluator may return multiple ranked candidates, but it must not dispatch any work.

## Test Requirements

Tests must cover:

- deterministic validation work recommends deterministic local tooling,
- bounded review work recommends local Ollama/GPU,
- planning work recommends ChatGPT planning,
- broad repo implementation recommends Codex Cloud/Web,
- local-runtime-required implementation can recommend Codex CLI with caution,
- boundary or classification decision recommends human review,
- recommendations include rationale and capacity notes,
- runtime artifacts are written,
- CLI JSON output is stable,
- no live provider/network/GPU calls occur,
- no dispatch queue mutation occurs,
- no Orchestrator runtime mutation occurs.

## Validation Rings

### Ring 0 - Static / Structural Validation

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\provider_routing_recommendations.py
Test-Path src\estate\core\provider_routing_recommendations_runtime.py
Test-Path tests\test_provider_routing_recommendations.py
Test-Path tests\test_provider_routing_recommendations_runtime.py
Test-Path docs\integration\provider_routing_recommendations.md
python -m py_compile src\estate\core\provider_routing_recommendations.py
python -m py_compile src\estate\core\provider_routing_recommendations_runtime.py
```

### Ring 1 - Deterministic Test Validation

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_provider_routing_recommendations.py tests/test_provider_routing_recommendations_runtime.py --basetemp Temp/pytest-provider-routing-recommendations
python -m estate.cli.main validate-work-package --id WP-0614 --json
```

Expected evidence:

```text
runtime/validation/work_packages/WP-0614_validation.json
operations/validation/reports/WP-0614_validation.md
collaboration/work_packages/completions/WP-0614_codex_done.json
```

### Ring 2 - Local GPU Reasoning Review

Reviewer questions:

```text
Did the implementation remain recommendations only?
Did it avoid scheduling, dispatch, assignment, and execution?
Did it include local RTX 4090/Ollama as a first-class recommendation candidate?
Did it protect Codex CLI capacity with clear escalation rules?
Did deterministic validation pass?
Did the completion receipt cover changed files, tests, limitations, and skipped live calls?
Were duplicate registries, dispatch queues, event systems, command surfaces, or offices introduced?
Is this ready for Chief Architect review?
```

Expected commands when available:

```powershell
Clear-Host
cd A:\theestate
python -m estate.cli.main local-gpu-validation-review --work-package WP-0614 --json
python -m estate.cli.main local-gpu-validation-review-report --work-package WP-0614
```

Expected evidence:

```text
runtime/validation/reviews/WP-0614_review.json
runtime/validation/reviews/WP-0614_review.md
```

### Ring 3 - CLI Escalation Validation

Use only when Ring 1 and Ring 2 are insufficient. Prefer read-only validation. Do not repair code unless explicitly assigned.

### Ring 4 - Institutional Acceptance

Chief Architect / Steward acceptance must confirm validation evidence, local review recommendation, unresolved concerns, and promotion or repair decision.

## Completion Receipt Requirements

If implemented by Codex or another provider, create:

```text
collaboration/work_packages/completions/WP-0614_codex_done.json
```

The receipt must include work_package_id, provider, files changed, tests run, validation commands run, runtime artifacts generated, docs updated, Office integration status, skipped live-provider calls, known limitations, and follow-up recommendations.

## Promotion Criteria

This package is ready for promotion when Ring 0 passes, Ring 1 passes, Ring 2 recommends Chief Architect review, Ring 3 is not required or completed, completion receipt is present, no blocking boundary issue remains, and Chief Architect / Steward acceptance is recorded.

## Completion Signal

If implemented by Codex, create the completion receipt and include validation ring evidence paths.
