# WP-0617 - Background Operations Event Runtime

Status: Proposed  
Priority: Critical  
Owner: Chief Architect  
Boundary Authority: Ingrid / Privacy and Boundary Office  
Primary Consumers: Office of the Steward, Traffic Controller / Operations Manager, Orchestrator Runtime Core, Execution Dispatch Queue, Execution Provider Adapter Contract, residents, workers, validation reviewers  
Classification: Estate Internal  
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is a broad repository implementation package for an event-driven background operations runtime. It should be implementable from repository context with deterministic tests. It must not require live provider calls, Codex CLI, ChatGPT CLI, Ollama, local GPU, browser automation, or network access in tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Implementation should be possible from repository context. Local deterministic validation is required after merge. Local runtime operation may later run on the Estate machine, but tests must use temporary paths and dry-run/no-live-provider behavior.
```

Capacity note:

```text
Use Codex Cloud/Web for implementation. Do not use Codex CLI unless Cloud/Web cannot complete the package or a local runtime issue must be diagnosed. Use deterministic local tooling for validation and local RTX 4090/Ollama for Ring 2 reasoning review.
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

Implement the first event-driven Background Operations Runtime for the Estate.

The Estate must not depend on the Steward manually prompting each participant for every update. It must support background operational movement: standing watches, event triggers, timed checks, staff update requests, validation review requests, and operation status refreshes.

This is not a turn-based chat loop. This is an event-driven operations loop.

The runtime should observe durable event/state artifacts, evaluate background operation rules, produce new operation events or requests, and surface status to the Office of the Steward. It must not execute live providers directly. It prepares governed work requests, review requests, movement candidates, and status updates for the existing institutional layers.

## 80/20 Direction

Build the useful 80 percent now:

```text
events/state change/time tick
  -> background operation rule evaluation
  -> generated operation request/update/review prompt artifact
  -> Office-visible background operations status
  -> optional dispatch-ready candidate through existing governed seams
```

Do not design a perfect distributed scheduler. Do not wait for every future resident/persona detail. Build the durable event-driven substrate so the Estate can start doing background coordination while remaining auditable and correctable.

## Architectural Clarification

The Estate is event-driven.

Avoid turn-based assumptions such as:

```text
The Steward asks A.
A answers.
The Steward asks B.
B answers.
```

The correct model is:

```text
An event occurs.
A standing watch or rule notices it.
The background operations runtime produces the next governed artifact.
Participants receive work/update/review requests through their proper channels.
The Office shows what is happening and what requires the Steward.
The Steward intervenes only where authority, boundary, or acceptance is required.
```

This package should allow background operations to happen while the Steward is not actively prompting each participant.

## Background

Current implemented chain includes:

```text
Operational Event Feed
Office Operational Activity Panel
Provider Catalog
Provider Health / Capacity
Worker Assignment Board
Traffic Controller / Operations Manager
Execution Provider Adapter Contract
Provider Routing Recommendations
Office Provider Routing Recommendations Panel
Execution Dispatch Queue
Codex Bridge
Execution Activity Surface
```

WP-0616 is intended to add a Traffic Controller movement decision loop. WP-0617 supplies the background event runtime that can notice when movement, review, validation, updates, or participant coordination is needed.

This package must integrate with existing event/status artifacts where possible and must not create a competing event feed if one already exists.

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
collaboration/work_packages/pending/WP-0601_Operational_Event_Feed_and_Office_Status.md
collaboration/work_packages/pending/WP-0608_Worker_Assignment_Board_Integration.md
collaboration/work_packages/pending/WP-0610_Traffic_Controller_Operations_Manager.md
collaboration/work_packages/pending/WP-0614_Execution_Provider_Routing_Recommendations.md
collaboration/work_packages/pending/WP-0615_Office_Provider_Routing_Recommendations_Panel.md
collaboration/work_packages/pending/WP-0616_Traffic_Controller_Movement_Decision_Loop.md
```

If any file is missing locally, record it in the completion receipt and continue with available canonical files.

## Scope

This package must implement:

1. Background operation event model.
2. Background operation rule/watch model.
3. Background operation request model.
4. Background operation runtime evaluator.
5. One-cycle deterministic runner for tests and manual operation.
6. Standing watches for stale validation, pending routing recommendations, pending movement decisions, provider capacity warnings, worker assignment gaps, and missing Ring 2 reviews.
7. Runtime artifact writer/loader for background operations events, requests, status, and reports.
8. Office-readable background operations status summary.
9. CLI commands for one-cycle evaluation, listing watches, listing generated requests, and status.
10. No-live-provider behavior with explicit generated request artifacts instead of direct provider calls.
11. Deterministic tests covering event-driven behavior.
12. Integration documentation.

## Out Of Scope

This package must not:

- run as an always-on daemon unless an existing service framework already supports it and tests remain deterministic,
- execute providers directly,
- call Codex CLI,
- call ChatGPT CLI,
- call Ollama,
- send emails or calendar invites,
- perform live network calls,
- bypass Traffic Controller / Operations Manager decisions,
- bypass the Execution Provider Adapter Contract,
- create a competing event feed if the existing operational event feed can be used,
- create a competing dispatch queue,
- create a new provider registry,
- create a new office,
- treat residents, workers, providers, or personas as interchangeable.

## Architectural Boundaries

This package must preserve:

```text
Events may trigger watches.
Watches may generate governed operation requests.
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
Background operations can create requests and status artifacts. Background operations cannot create institutional truth, approve boundary decisions, or execute providers without the proper governed seam.
```

## Expected Artifacts

Expected implementation artifacts:

```text
src/estate/core/background_operations.py
src/estate/core/background_operations_runtime.py
tests/test_background_operations.py
tests/test_background_operations_runtime.py
docs/integration/background_operations_event_runtime.md
```

Expected integration touchpoints, if clean and low-risk:

```text
src/estate/cli/main.py
src/estate/core/operational_events.py
src/estate/core/steward_command_center.py
src/estate/core/provider_routing_recommendations_runtime.py
src/estate/core/provider_routing_office_panel.py
src/estate/core/traffic_controller_movement_runtime.py
src/estate/core/worker_assignments.py
src/estate/core/provider_health.py
src/estate/core/work_package_validation.py
```

Do not create duplicate event feeds, provider catalogs, dispatch queues, or Office command systems.

## Runtime Artifacts

Use local runtime paths:

```text
runtime/background_operations/events.jsonl
runtime/background_operations/requests/<request_id>.json
runtime/background_operations/status/latest.json
runtime/background_operations/status/summary.json
runtime/background_operations/reports/latest.md
runtime/background_operations/watches.json
```

If existing operational event feed helpers exist, write compatible events into the existing feed as well, or document why that integration was not possible.

Do not commit live runtime outputs unless explicitly required as evidence.

## Event Model Requirements

Background operation events should include:

```text
event_id
event_type
source
source_artifact
subject_type
subject_id
classification
created_at
summary
payload
metadata
```

Suggested event types:

```text
time_tick
artifact_changed
recommendation_created
movement_decision_needed
validation_stale
ring2_review_needed
provider_capacity_warning
assignment_gap_detected
background_request_created
background_request_completed
background_request_blocked
```

## Watch Model Requirements

Background operation watches should include:

```text
watch_id
name
enabled
trigger_type
source_paths
conditions
action_type
cooldown_seconds
classification
last_triggered_at
metadata
```

Required initial watches:

```text
pending_routing_recommendation_watch
missing_ring2_review_watch
stale_validation_artifact_watch
provider_capacity_warning_watch
worker_assignment_gap_watch
pending_movement_decision_watch
```

## Request Model Requirements

Background operation requests should include:

```text
request_id
request_type
source_event_id
watch_id
target_role
target_subsystem
recommended_provider
requires_human_review
requires_boundary_review
priority
classification
summary
requested_action
source_artifacts
created_at
status
metadata
```

Suggested request types:

```text
staff_update_request
validation_review_request
traffic_controller_review_request
routing_review_request
provider_capacity_review_request
worker_assignment_review_request
steward_attention_request
```

## Runtime Behavior Requirements

Implement a deterministic one-cycle runner that:

1. Loads watches.
2. Loads relevant runtime/status artifacts.
3. Evaluates enabled watches.
4. Creates background operation events and requests for triggered watches.
5. Applies cooldowns to avoid repeated spam.
6. Writes latest status and summary artifacts.
7. Returns JSON for CLI use.
8. Does not call live providers.
9. Does not mutate dispatch queues except through explicitly allowed existing preparation helpers, if any.
10. Does not make authority decisions.

## CLI Requirements

Add CLI commands consistent with existing command style. Suggested names:

```text
python -m estate.cli.main background-operations cycle --json
python -m estate.cli.main background-operations watches --json
python -m estate.cli.main background-operations requests --json
python -m estate.cli.main background-operations status --json
python -m estate.cli.main background-operations report
```

If existing CLI naming convention suggests different names, follow repository convention and document the actual commands.

## Office / Command Center Requirements

If command-center integration exists, surface:

```text
background_operations_available
active_watches_count
generated_requests_count
blocked_requests_count
stale_validation_count
ring2_review_needed_count
pending_movement_decision_count
provider_capacity_warning_count
worker_assignment_gap_count
latest_background_request
latest_background_event
warnings
```

Do not add fake controls. Every exposed verb must be real.

## Character / Resident Boundary Note

This package must support background coordination without making character-development assumptions.

It must not:

```text
create resident identity state
create character cards
create persona files
invent memory
blur resident, worker, provider, persona, and office roles
```

If a background request concerns resident identity, persona-sensitive material, character continuity, or source classification, mark it as requiring Ingrid/Steward or appropriate Chief Architect review.

## Test Requirements

Tests must cover:

- one-cycle runner produces no requests when no watch is triggered,
- pending routing recommendation creates review request,
- missing Ring 2 review creates validation review request,
- stale validation artifact creates review request,
- provider capacity warning creates provider-capacity request,
- worker assignment gap creates assignment review request,
- pending movement decision creates Traffic Controller review request,
- cooldown prevents repeated duplicate requests,
- status summary is written,
- Office payload reflects background operations status if integrated,
- no live provider/network/GPU calls occur,
- no provider execution occurs,
- no dispatch execution occurs,
- no duplicate event feed/provider registry/dispatch queue/office is introduced,
- resident/character-sensitive request is flagged for review rather than acted on.

## Validation Rings

### Ring 0 - Static / Structural Validation

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\background_operations.py
Test-Path src\estate\core\background_operations_runtime.py
Test-Path tests\test_background_operations.py
Test-Path tests\test_background_operations_runtime.py
Test-Path docs\integration\background_operations_event_runtime.md
python -m py_compile src\estate\core\background_operations.py
python -m py_compile src\estate\core\background_operations_runtime.py
```

### Ring 1 - Deterministic Test Validation

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_background_operations.py tests/test_background_operations_runtime.py --basetemp Temp/pytest-background-operations
python -m estate.cli.main validate-work-package --id WP-0617 --json
```

Expected evidence:

```text
runtime/validation/work_packages/WP-0617_validation.json
operations/validation/reports/WP-0617_validation.md
collaboration/work_packages/completions/WP-0617_codex_done.json
```

### Ring 2 - Local GPU Reasoning Review

Reviewer questions:

```text
Did this package correctly treat the Estate as event-driven, not turn-based?
Did it enable useful background operations without direct provider execution?
Did it create governed requests/status artifacts rather than unauthorized decisions?
Did it preserve Traffic Controller / Operations Manager as movement decision layer?
Did it preserve the Execution Provider Adapter Contract as provider handoff seam?
Did it avoid duplicate event feeds, provider registries, dispatch queues, or offices?
Did it avoid character/resident identity assumptions?
Did deterministic validation pass?
Is this ready for Chief Architect review?
```

Expected commands when available:

```powershell
Clear-Host
cd A:\theestate
python -m estate.cli.main local-gpu-validation-review --work-package WP-0617 --json
python -m estate.cli.main local-gpu-validation-review-report --work-package WP-0617
```

Expected evidence:

```text
runtime/validation/reviews/WP-0617_review.json
runtime/validation/reviews/WP-0617_review.md
```

### Ring 3 - CLI Escalation Validation

Use only when Ring 1 and Ring 2 are insufficient. Prefer read-only validation. Do not repair code unless explicitly assigned.

### Ring 4 - Institutional Acceptance

Chief Architect / Steward acceptance must confirm validation evidence, local review recommendation, unresolved concerns, and promotion or repair decision.

## Completion Receipt Requirements

If implemented by Codex or another provider, create:

```text
collaboration/work_packages/completions/WP-0617_codex_done.json
```

The receipt must include work_package_id, provider, files changed, tests run, validation commands run, runtime artifacts generated, docs updated, Office integration status, skipped live-provider calls, known limitations, and follow-up recommendations.

## Promotion Criteria

This package is ready for promotion when Ring 0 passes, Ring 1 passes, Ring 2 recommends Chief Architect review, Ring 3 is not required or completed, completion receipt is present, no blocking boundary issue remains, and Chief Architect / Steward acceptance is recorded.

## Completion Signal

If implemented by Codex, create the completion receipt and include validation ring evidence paths.
