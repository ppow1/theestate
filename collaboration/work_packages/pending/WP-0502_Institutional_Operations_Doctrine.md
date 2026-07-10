# WP-0502 - Institutional Operations Doctrine

Status: Proposed
Priority: High
Owner: Chief Architect #5
Coordinating Offices: Chief Architect #6 / Operations Architecture, Character Architecture, Steward
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Chief Architect, Operations Architecture, Character Architecture, Engineering, Traffic Controller / Operations Manager, Execution Provider Infrastructure, Background Operations, Office of the Steward
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository doctrine, documentation, and deterministic validation work. It should not require local GPU access, live provider execution, Codex CLI capacity, model calls, or network-dependent tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Repository context is sufficient for baseline completion. Local validation may be performed after merge.
```

Capacity note:

```text
Use Codex Cloud/Web. Do not use Codex CLI unless repository state is ambiguous or local runtime evidence contradicts repository artifacts.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, queues, providers, event systems, runtime services, command surfaces, or autonomous authorities.

Do not perform live provider calls.

Codify the doctrine. Do not invent a new operating system for the Estate.
```

## Mission

Create a formal Estate doctrine artifact that captures the institutional operating principles that emerged through coordination between Operations Architecture, Execution and Operations Infrastructure, Character Architecture, and Steward guidance.

The doctrine should preserve the recurring architectural invariants now validated by WP-0501 and reinforced by the 061x Operations Runtime wave.

The doctrine must become inherited guidance for future work packages rather than remaining buried in conversation history or individual package reports.

## Background

The recent operations and execution-provider merge wave established a stable institutional stack:

```text
Runtime computes.
Operations conducts.
Traffic Controller constrains.
Execution Providers implement.
Steward governs.
```

Additional stable principles emerged:

```text
Operations conducts movement.
Traffic Controller authorizes movement according to governance.
Authority flows downward.
Evidence flows upward.
The runtime never becomes the resident.
The resident never becomes the runtime.
Recommendations are evidence, not decisions.
Validation results are evidence, not institutional acceptance.
Dispatch remains the governed implementation path.
```

WP-0501 validated the execution-provider boundary after the WP-0614 through WP-0619 merge wave. It confirmed that provider recommendations remained advisory, Office provider-routing panels remained visibility-only, Background Operations did not become an execution provider, Dispatch Queue was not replaced, and validation evidence remained distinct from institutional acceptance.

This package should elevate those principles into a durable doctrine document.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/architecture/execution_provider_boundary_review_after_background_operations_merge_wave.md
operations/validation/reports/WP-0501_execution_provider_boundary_review.md
collaboration/work_packages/completions/WP-0501_codex_done.json
docs/integration/execution_provider_adapter_contract.md
docs/integration/provider_routing_recommendations.md
docs/integration/provider_routing_office_panel.md
docs/integration/background_operations_event_runtime.md
docs/integration/background_operational_targets_and_post_merge_audit.md
docs/integration/operations_runtime_service_loop.md
```

If any file is missing locally, record it and continue with available canonical files.

## Scope

This package must create a doctrine artifact that defines and explains:

1. The institutional layer model.
2. The runtime / operations / traffic control / execution provider / governance stack.
3. The movement authority model.
4. The authority downward / evidence upward model.
5. The resident / runtime separation model.
6. The recommendation / decision separation model.
7. The validation / acceptance separation model.
8. Dispatch as the governed implementation path.
9. Provider infrastructure as implementation substrate beneath Operations.
10. Background Operations as mechanical infrastructure, not institutional authority.
11. Operations Manager as an operational executive acting within delegated governance.
12. Traffic Controller as movement constraint and authorization enforcement.
13. Steward as doctrine, governance, and exception authority.
14. How future work packages should inherit this doctrine.
15. How violations should be treated as boundary findings rather than local preferences.

## Out Of Scope

This package must not:

- create a new office;
- create a new runtime service;
- create a new queue;
- create a new registry;
- create a new event system;
- create a new provider;
- create a new command surface;
- modify provider execution behavior;
- modify Background Operations behavior;
- modify Dispatch Queue behavior;
- modify Traffic Controller authority;
- modify Operations Manager runtime behavior;
- modify Steward authority;
- schedule work;
- dispatch work;
- assign workers;
- execute providers;
- perform live model, GPU, network, Codex CLI, ChatGPT CLI, or Ollama calls.

## Expected Artifacts

Create the primary doctrine artifact at one of the following paths, preferring governance if consistent with repository conventions:

```text
docs/governance/Institutional_Operations_Doctrine.md
```

If repository conventions strongly favor architecture documents, use:

```text
docs/architecture/institutional_operations_doctrine.md
```

Do not create both unless there is already a clear convention for mirrored doctrine summaries.

Create a completion receipt:

```text
collaboration/work_packages/completions/WP-0502_codex_done.json
```

If consistent with existing validation conventions, add a deterministic validation recipe for:

```text
WP-0502
```

Likely file:

```text
src/estate/core/work_package_validation.py
```

If adding a validation recipe is too broad or conflicts with current validation architecture, document the reason rather than forcing it.

## Doctrine Requirements

The doctrine document must include these exact principles:

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
Authority flows downward.
Evidence flows upward.
```

```text
The runtime never becomes the resident.
The resident never becomes the runtime.
```

```text
Recommendations are evidence, not decisions.
Validation results are evidence, not institutional acceptance.
Dispatch remains the governed implementation path.
```

The doctrine must also explain the practical meaning of each principle and include examples of allowed and prohibited interpretations.

## Boundary Requirements

The doctrine must make clear that:

- Runtime may compute state, run watches, evaluate dependencies, produce telemetry, and generate governed requests.
- Runtime may not become a resident, provider, dispatcher, governance authority, or acceptance authority.
- Operations may conduct approved operational work.
- Operations may not bypass Traffic Controller constraints or Dispatch.
- Traffic Controller authorizes movement according to governance.
- Execution Providers implement through provider seams.
- Provider Routing Recommendations are advisory evidence only.
- Dispatch Queue remains the single governed implementation path.
- Audit and Validation produce evidence, not institutional truth.
- Chief Architect and Steward acceptance remain distinct from validation output.
- Residents operate within role boundaries and do not become runtime infrastructure.
- Future work packages inherit this doctrine unless explicitly superseded by Steward-approved governance.

## Validation Expectations

Run deterministic validation where available.

Likely commands:

```text
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0501 --json
```

If WP-0502 validation recipe is added, also run:

```text
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0502 --json
```

If targeted tests are added, run the relevant pytest command. Do not add brittle repository-wide word scans. Tests should validate doctrine artifact existence, required principle text, receipt completeness, and non-execution claims.

## Completion Receipt Requirements

The completion receipt must include:

```text
work_package_id
status
owner
coordinating_offices
files_reviewed
files_created
implementation_files_modified
validation_commands_run
validation_results
doctrine_principles_recorded
boundary_verdicts
live_provider_calls_made
runtime_behavior_modified
operations_behavior_modified
traffic_controller_behavior_modified
dispatch_behavior_modified
provider_behavior_modified
governance_behavior_modified
known_limitations
ready_for_ca_review
```

The receipt must explicitly state:

```text
live_provider_calls_made: false
```

If only documentation and validation recipe support were added, say so clearly.

## Acceptance Criteria

This package is complete when:

1. A doctrine artifact exists.
2. The doctrine includes the exact principles listed in this work package.
3. The doctrine explains institutional layers, movement authority, evidence flow, resident/runtime separation, recommendation/decision separation, validation/acceptance separation, and Dispatch integrity.
4. The doctrine gives future work packages clear inheritance guidance.
5. No new office, runtime, queue, registry, provider, event system, command surface, or authority layer is created.
6. Completion receipt exists.
7. Deterministic validation was run or unavailable validation was documented.
8. No live provider calls were required.
9. No execution, dispatch, provider, runtime, operations, Traffic Controller, or governance behavior was modified except optional validation-recipe registration.
10. The package is ready for Chief Architect / Steward doctrine review.

## Steward / Chief Architect Note

This is a CA5 500-series package because it codifies doctrine emerging from execution and operations infrastructure boundary work.

It must coordinate with CA6 Operations Architecture and Character Architecture, but it must not take over their lanes.

The goal is to preserve institutional responsibility boundaries as the Estate becomes more operationally alive.
