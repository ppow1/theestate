# WP-0616 - Traffic Controller Movement Decision Loop

Status: Proposed  
Priority: Critical  
Owner: Chief Architect  
Boundary Authority: Ingrid / Privacy and Boundary Office  
Primary Consumers: Traffic Controller / Operations Manager, Office of the Steward, Orchestrator Runtime Core, Execution Dispatch Queue, Execution Provider Adapter Contract  
Classification: Estate Internal  
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is a broad repository implementation package that wires together existing operational subsystems. It should be implemented by Codex Cloud/Web when capacity is available. It should not require Codex CLI, live provider execution, local GPU access, browser automation, or network access in tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation should be possible from repository context. Local deterministic validation is required after merge. Local RTX 4090/Ollama Ring 2 review should examine whether the movement loop preserves institutional boundaries.
```

Capacity note:

```text
Use Codex Cloud/Web for implementation. Do not use Codex CLI unless the implementation cannot be completed without local runtime context. Use deterministic local tooling for validation and local GPU review for architectural/boundary validation.
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

Implement the first governed Traffic Controller movement decision loop.

The Estate now has routing recommendations, an Office panel for those recommendations, an execution dispatch queue, and an execution provider adapter contract. The next operational step is to let the Traffic Controller / Operations Manager turn a recommendation into a recorded movement decision and, when approved, create the appropriate dispatch-ready artifact without executing any provider.

This package moves the Estate from passive visibility toward command-center operation. It must provide real verbs and real artifacts.

## 80/20 Direction

This package should implement the useful 80 percent of the movement loop now:

```text
recommendation -> Traffic Controller decision -> dispatch candidate / adapter request artifact -> validation evidence -> Office-readable movement status
```

Do not wait for perfect orchestration policy. Do not design a complete future scheduler. Build the governed movement seam and allow later packages to refine it.

## Background

Current implemented chain:

```text
Planning Provider Framework
Operational Event Feed
Office Operational Activity Panel
Orchestrator Intake Contract
Provider Catalog
Provider Health / Capacity
Worker Assignment Board
Orchestrator Runtime Core
Traffic Controller / Operations Manager
Execution Provider Adapter Contract
Provider Routing Recommendations
Office Provider Routing Recommendations Panel
Execution Dispatch Queue
Codex Bridge
Execution Activity Surface
```

Accepted institutional boundary:

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

WP-0616 must connect the recommendation layer to a governed movement decision and dispatch-ready artifact while preserving these boundaries.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/workers/templates/Codex_Work_Package_Template_v1.md
docs/integration/provider_routing_recommendations.md
docs/integration/provider_routing_office_panel.md
docs/integration/execution_provider_adapter_contract.md
collaboration/work_packages/pending/WP-0610_Traffic_Controller_Operations_Manager.md
collaboration/work_packages/pending/WP-0613_Execution_Provider_Adapter_Contract.md
collaboration/work_packages/pending/WP-0614_Execution_Provider_Routing_Recommendations.md
collaboration/work_packages/pending/WP-0615_Office_Provider_Routing_Recommendations_Panel.md
docs/governance/workers/WP-EXECUTION-DISPATCH-QUEUE-001.md
```

If any file is missing locally, record it in the completion receipt and continue with available canonical files.

## Scope

This package must implement:

1. Traffic Controller movement decision model.
2. Movement decision runtime writer/loader.
3. Decision verbs for approve, hold, reject, request-boundary-review, request-revision, and defer.
4. Conversion from approved provider routing recommendation to dispatch candidate or adapter request artifact.
5. Office-readable movement status summary.
6. CLI commands to record and list movement decisions.
7. CLI command to prepare dispatch-ready artifact from an approved movement decision.
8. Validation that recommendations remain advisory until a movement decision exists.
9. Validation that approved movement still does not execute providers.
10. Documentation showing the movement loop and boundary rules.
11. Deterministic tests covering decision states, conversion, blocked cases, and no live provider calls.

## Out Of Scope

This package must not:

- execute providers,
- call Codex CLI,
- call ChatGPT CLI,
- call Ollama,
- implement autonomous scheduling,
- implement routing policy,
- allow routing recommendations to move work without a Traffic Controller decision,
- bypass the Execution Provider Adapter Contract,
- create a new provider registry,
- create a new dispatch queue if an existing execution dispatch queue is present,
- create a new event system,
- create a new office,
- rewrite Orchestrator Runtime Core.

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
A recommendation cannot move work. A Traffic Controller movement decision can authorize preparation of a dispatch-ready artifact. Preparing a dispatch-ready artifact is not provider execution.
```

## Expected Artifacts

Expected implementation artifacts:

```text
src/estate/core/traffic_controller_movement.py
src/estate/core/traffic_controller_movement_runtime.py
tests/test_traffic_controller_movement.py
tests/test_traffic_controller_movement_runtime.py
docs/integration/traffic_controller_movement_decision_loop.md
```

Expected integration touchpoints, if clean and low-risk:

```text
src/estate/cli/main.py
src/estate/core/provider_routing_recommendations.py
src/estate/core/provider_routing_recommendations_runtime.py
src/estate/core/provider_routing_office_panel.py
src/estate/core/execution_provider_adapter.py
src/estate/core/execution_provider_adapter_runtime.py
src/estate/core/execution_dispatch_queue.py
src/estate/core/steward_command_center.py
src/estate/core/work_package_validation.py
```

Do not create duplicate provider catalogs, duplicate dispatch queues, duplicate routing engines, duplicate event feeds, or duplicate Office command systems.

## Runtime Artifacts

Use local runtime paths:

```text
runtime/traffic_controller/movement/decisions/<decision_id>.json
runtime/traffic_controller/movement/status/latest.json
runtime/traffic_controller/movement/status/summary.json
runtime/traffic_controller/movement/reports/<decision_id>.md
```

If preparing adapter request artifacts, use the WP-0613 runtime locations:

```text
runtime/execution_adapters/requests/<request_id>.json
runtime/execution_adapters/status/latest.json
runtime/execution_adapters/status/summary.json
```

If an existing execution dispatch queue writer exists, use it rather than creating a parallel queue.

## Movement Decision Model Requirements

Movement decision fields should include:

```text
decision_id
recommendation_id
routing_request_id
work_package_id
source_artifact
decision
status
recommended_provider
selected_provider
provider_rationale
capacity_note
local_runtime_required
human_review_required
boundary_review_required
validation_rings_required
traffic_controller_notes
steward_reference
created_at
decided_by
prepared_dispatch_artifact
prepared_adapter_request
metadata
```

Allowed movement decisions:

```text
approve
hold
reject
request_boundary_review
request_revision
defer
```

Allowed movement statuses:

```text
recorded
blocked
prepared_for_dispatch
held
rejected
deferred
needs_boundary_review
needs_revision
```

## Movement Rules

Implement deterministic rules:

```text
A routing recommendation by itself cannot create dispatch or adapter artifacts.
Only an approve decision can prepare dispatch-ready artifacts.
Human review recommendations require a human/Traffic Controller decision before preparation.
Boundary review requirements block preparation unless decision explicitly records boundary review reference.
Held, rejected, deferred, and revision-requested decisions cannot prepare dispatch artifacts.
Prepared artifacts must be provider-neutral and pass through Execution Provider Adapter Contract shape where applicable.
Provider execution must not occur in this package.
```

## CLI Requirements

Add CLI commands consistent with existing command style. Suggested names:

```text
python -m estate.cli.main traffic-movement decide --recommendation <path> --decision approve --selected-provider codex_cloud_web --json
python -m estate.cli.main traffic-movement list --json
python -m estate.cli.main traffic-movement prepare --decision-id <decision_id> --json
python -m estate.cli.main traffic-movement status --json
```

If existing CLI naming convention suggests different names, follow repository convention and document the actual commands.

## Office / Command Center Requirements

If a command-center payload exists, surface:

```text
movement_available
pending_recommendations_count
approved_movements_count
held_movements_count
blocked_movements_count
latest_decision
latest_prepared_artifact
warnings
advisory_boundary_note
```

Do not add fake buttons or unsupported verbs. Every exposed verb must be real.

## Test Requirements

Tests must cover:

- recommendation remains advisory without decision,
- approve decision can be recorded,
- hold decision blocks preparation,
- reject decision blocks preparation,
- defer decision blocks preparation,
- request-boundary-review decision blocks preparation,
- request-revision decision blocks preparation,
- approve with missing required boundary reference is blocked when boundary review is required,
- approve prepares provider-neutral dispatch or adapter request artifact,
- prepared artifact uses existing adapter contract shape,
- no provider execution occurs,
- no live provider/network/GPU calls occur,
- Office/command-center summary reflects decisions if integrated,
- duplicate provider registry/dispatch queue/event system is not introduced.

## Validation Rings

### Ring 0 - Static / Structural Validation

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\traffic_controller_movement.py
Test-Path src\estate\core\traffic_controller_movement_runtime.py
Test-Path tests\test_traffic_controller_movement.py
Test-Path tests\test_traffic_controller_movement_runtime.py
Test-Path docs\integration\traffic_controller_movement_decision_loop.md
python -m py_compile src\estate\core\traffic_controller_movement.py
python -m py_compile src\estate\core\traffic_controller_movement_runtime.py
```

### Ring 1 - Deterministic Test Validation

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_traffic_controller_movement.py tests/test_traffic_controller_movement_runtime.py --basetemp Temp/pytest-traffic-controller-movement
python -m estate.cli.main validate-work-package --id WP-0616 --json
```

Expected evidence:

```text
runtime/validation/work_packages/WP-0616_validation.json
operations/validation/reports/WP-0616_validation.md
collaboration/work_packages/completions/WP-0616_codex_done.json
```

### Ring 2 - Local GPU Reasoning Review

Reviewer questions:

```text
Did this package make real progress toward a command-center operating loop?
Did it preserve routing as advisory until Traffic Controller decision?
Did it prevent movement without an approve decision?
Did it prevent provider execution?
Did it use the WP-0613 adapter contract rather than bypassing it?
Did it avoid duplicate registries, dispatch queues, event systems, or offices?
Did deterministic validation pass?
Is this ready for Chief Architect review?
```

Expected commands when available:

```powershell
Clear-Host
cd A:\theestate
python -m estate.cli.main local-gpu-validation-review --work-package WP-0616 --json
python -m estate.cli.main local-gpu-validation-review-report --work-package WP-0616
```

Expected evidence:

```text
runtime/validation/reviews/WP-0616_review.json
runtime/validation/reviews/WP-0616_review.md
```

### Ring 3 - CLI Escalation Validation

Use only when Ring 1 and Ring 2 are insufficient. Prefer read-only validation. Do not repair code unless explicitly assigned.

### Ring 4 - Institutional Acceptance

Chief Architect / Steward acceptance must confirm validation evidence, local review recommendation, unresolved concerns, and promotion or repair decision.

## Completion Receipt Requirements

If implemented by Codex or another provider, create:

```text
collaboration/work_packages/completions/WP-0616_codex_done.json
```

The receipt must include work_package_id, provider, files changed, tests run, validation commands run, runtime artifacts generated, docs updated, Office integration status, skipped live-provider calls, known limitations, and follow-up recommendations.

## Promotion Criteria

This package is ready for promotion when Ring 0 passes, Ring 1 passes, Ring 2 recommends Chief Architect review, Ring 3 is not required or completed, completion receipt is present, no blocking boundary issue remains, and Chief Architect / Steward acceptance is recorded.

## Completion Signal

If implemented by Codex, create the completion receipt and include validation ring evidence paths.
