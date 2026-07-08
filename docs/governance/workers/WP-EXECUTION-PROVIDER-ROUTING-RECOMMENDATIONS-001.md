# WP-EXECUTION-PROVIDER-ROUTING-RECOMMENDATIONS-001 - Execution Provider Routing Recommendations and Local GPU Decomposition

Status: Proposed
Priority: High
Owner: Chief Architect / Steward
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Office of the Steward, Alfred, Helen, Traffic Controller / Operations Manager, future mechanical coordination layers, execution providers
Classification: Estate Internal
Created: 2026-07-08

## Supersedes

This package supersedes the paused package:

```text
WP-EXECUTION-PROVIDER-ROUTING-001
```

Reason: the earlier title and wording used policy/routing language that could imply scheduling or autonomous choice. This revised package is explicitly recommendation-only.

## Codex Command

Read this work package and do exactly what it says.

Do not schedule work.

Do not dispatch work.

Do not assign workers.

Do not execute providers.

Do not implement autonomous provider choice.

Do not replace the Traffic Controller / Operations Manager.

Do not bypass Steward, Ingrid, Audit, or Validation.

Do not ignore local RTX 4090 / Ollama capacity.

## Mission

Implement the first execution-provider routing recommendation layer for The Estate.

This layer produces provider-fit recommendation metadata only.

It helps humans and future mechanical coordination layers understand whether work appears better suited for:

- Codex Cloud/Web
- Codex CLI
- ChatGPT / planning lane
- local Ollama / RTX 4090 GPU lane
- deterministic local tools such as PowerShell, Python, pytest, and validation commands
- human / Ingrid / Steward review

The layer does not make final movement decisions. It does not schedule. It does not dispatch. It does not execute.

## Background

The Estate observed that Codex CLI can complete real implementation work, but may burn Codex seat capacity quickly when used for large local command-line implementation packages.

The Estate also has a local RTX 4090 capable of running local LLMs through Ollama. Local GPU execution should be treated as a first-class candidate for smaller, bounded, low-risk subtasks.

The refined operating principle is:

```text
Large conceptual or broad repo implementation work -> Codex Cloud/Web or ChatGPT planning lane
Local-runtime-required implementation -> Codex CLI only when justified
Small bounded decomposition/review/parsing/preflight tasks -> local Ollama / RTX 4090
Deterministic validation and file checks -> local tools
Boundary and authority decisions -> Steward / Ingrid / human review
```

## Relationship To Future Mechanical Coordination Layers

The routing recommendation layer may be consumed by a future scheduling or orchestration layer, but it does not implement either one.

It produces recommendation metadata.

It does not move work between queues.

It does not approve work.

It does not choose a provider autonomously.

It does not assign workers.

It does not invoke an execution provider adapter.

## Planning-To-Dispatch Boundary

Planning providers may propose decomposition and provider-fit candidates.

Routing recommendations may evaluate provider fit.

Traffic Controller / Operations Manager or the Steward decides movement.

Dispatch queues hold candidate work.

Future mechanical coordination layers may apply approved movement rules.

Execution provider adapters perform actual provider handoff.

Safe path:

```text
Planning Provider
-> decomposition candidates
-> provider-fit recommendation metadata
-> human / Traffic Controller review
-> intake or dispatch queue artifact
-> future mechanical coordination layer
-> execution provider adapter
```

Planning output must not jump directly into live execution.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/architecture/execution_provider_operational_visibility_requirements.md
docs/architecture/execution_provider_codex_cli_mapping.md
docs/integration/execution_activity_surface_usage.md
docs/integration/execution_dispatch_queue_usage.md
docs/governance/workers/WP-EXECUTION-DISPATCH-QUEUE-001.md
```

If any file is missing locally, record it in the implementation report and continue with available canonical files.

## Scope

Implement a local routing recommendation module that supports:

1. A provider-fit recommendation request model.
2. A provider-fit recommendation result model.
3. Rule-based recommendation metadata for Cloud/Web, CLI, local GPU, ChatGPT planning, deterministic tools, and human review.
4. Task decomposition recommendations for work that can be split into local-GPU-sized subtasks.
5. Capacity-aware fields for labels such as `A2C1`, `A2C2`, `A2C3`.
6. Local GPU capability fields for RTX 4090 / Ollama models.
7. Optional metadata integration with the Execution Dispatch Queue.
8. Current routing recommendation summary output for Office visibility.
9. Tests that do not require live provider execution.

## Out Of Scope

This package must not:

- execute live Codex, ChatGPT, or Ollama calls
- require live GPU calls in tests
- implement autonomous scheduling
- implement provider dispatch
- implement worker assignment
- implement multi-seat auto-rotation
- scrape browser usage pages
- create a new Office
- modify Alfred, Helen, Ingrid, or Traffic Controller authority
- store credentials, auth files, browser profile data, or tokens

## Recommendation Categories

Support these recommendation labels at minimum:

```text
codex_cloud_web
codex_cli
chatgpt_planning
local_ollama_gpu
deterministic_local_tooling
human_review
blocked_needs_policy
```

## Planning Metadata Shape

Support or document planning-output fields that may feed routing recommendations:

```text
planning_artifact_id
source_work_package
mission
decomposition_items
required_capabilities
candidate_provider_types
candidate_provider_ids
local_runtime_required
repo_write_required
network_required
human_review_required
boundary_review_required
validation_required
estimated_complexity
estimated_context_size
expected_artifacts
allowed_paths
forbidden_paths
classification
risk_notes
routing_notes
```

For each decomposition item, support fields such as:

```text
item_id
summary
recommended_provider_fit
why_not_local
why_not_codex_cli
why_not_codex_cloud
why_not_ollama
requires_repo_write
requires_local_runtime
requires_large_context
requires_external_connector
requires_human_approval
validation_expectation
```

## Recommendation Request Model

Create or support a recommendation request with fields such as:

```json
{
  "recommendation_id": "route_001",
  "work_package_id": "WP-EXAMPLE",
  "task_title": "Implement focused parser tests",
  "task_type": "implementation",
  "conceptual_complexity": "medium",
  "repo_change_size": "small",
  "local_runtime_required": false,
  "needs_broad_repo_context": false,
  "requires_tests": true,
  "requires_gpu": false,
  "security_classification": "Estate Internal",
  "estimated_context_size": "small",
  "estimated_provider_burn": "low",
  "preferred_profile_label": "A2C3",
  "available_local_models": ["qwen2.5-coder:7b", "qwen3:8b", "llama3:8b"],
  "capacity_notes": []
}
```

## Recommendation Result Model

Return recommendation results with fields such as:

```json
{
  "recommendation_id": "route_001",
  "recommended_provider_fit": "local_ollama_gpu",
  "alternate_provider_fits": ["codex_cloud_web"],
  "allowed_provider_fits": ["local_ollama_gpu", "codex_cloud_web", "human_review"],
  "not_recommended_provider_fits": ["codex_cli"],
  "reason": "Small bounded implementation review can be decomposed for local GPU preflight before cloud execution.",
  "decomposition_recommended": true,
  "suggested_subtasks": [],
  "capacity_warning": false,
  "human_attention_required": false,
  "final_decision_authority": "Traffic Controller / Operations Manager or Steward"
}
```

## Recommendation Rules

Implement initial deterministic recommendation rules:

1. Broad conceptual planning should recommend `chatgpt_planning` or `codex_cloud_web`.
2. Broad repo implementation should prefer `codex_cloud_web` over `codex_cli` unless local runtime is required.
3. Local runtime integration, Windows path behavior, local validation, local Ollama/GPU behavior, and A-drive-specific tasks may recommend `codex_cli`.
4. Small bounded review, parsing, summarization, prompt cleanup, fixture generation, test-data generation, and decomposition tasks should recommend `local_ollama_gpu` when security allows.
5. Deterministic checks, validation commands, JSON/schema checks, file existence checks, and pytest runs should recommend `deterministic_local_tooling`.
6. Sensitive boundary questions should recommend `human_review` or `blocked_needs_policy`.
7. If a seat/profile has low capacity, Codex-related recommendations should include a capacity warning.

## Local GPU Decomposition

When a task is too large for local Ollama but contains smaller bounded pieces, recommend decomposition.

Examples of GPU-sized subtasks:

- summarize one source file
- inspect one test file
- generate test cases for one module
- classify a work package by provider fit
- review a small diff
- extract acceptance criteria from one package
- draft a deterministic prompt from one package
- check whether a completion receipt is complete

The module should produce suggested subtasks without executing them.

## Runtime Paths

Use local runtime storage by default:

```text
runtime/execution_routing/current.json
runtime/execution_routing/report.md
runtime/execution_routing/recommendations.jsonl
```

Do not commit live runtime outputs.

## Expected Artifacts

Create or update only paths justified by the existing codebase.

Expected implementation artifacts:

```text
src/estate/core/execution_routing.py
tests/test_execution_routing.py
docs/integration/execution_provider_routing_recommendations_usage.md
```

Likely integration touchpoints, if clean and low-risk:

```text
src/estate/cli/main.py
src/estate/core/execution_dispatch.py
src/estate/core/steward_command_center.py
src/estate/core/operator_activity_stream.py
src/estate/core/work_package_validation.py
```

## CLI Requirements

If CLI wiring is straightforward, expose commands such as:

```text
python -m estate.cli.main execution-routing recommend --file <request.json> --json
python -m estate.cli.main execution-routing-report
```

If CLI wiring is not straightforward, implement documented Python entry points and defer CLI wiring.

## Dispatch Queue Integration

If the Execution Dispatch Queue is present, add recommendation metadata fields or helper functions so a dispatch item can carry:

- recommended provider fit
- allowed provider fits
- not-recommended provider fits
- recommendation reason
- decomposition recommended
- suggested subtasks
- provider capacity warning

Do not make dispatch queue items executable merely because recommendation metadata exists.

Do not break existing dispatch queue tests.

## Office Visibility

Generate a routing recommendation summary suitable for the Office of the Steward.

At minimum, the summary should show:

- how many tasks are recommended for Codex Cloud/Web
- how many tasks are recommended for Codex CLI
- how many tasks are recommended for local Ollama/GPU
- how many tasks are recommended for deterministic local tooling
- how many tasks need human review
- any capacity warnings

If the existing Office command center has a clear pattern, add a minimal panel/status hook. Do not rewrite the Office UI.

## Test Requirements

Tests must cover:

- broad conceptual work routes away from CLI
- large repo implementation prefers Codex Cloud/Web
- local-runtime-required work may recommend Codex CLI
- small bounded subtasks prefer local Ollama/GPU
- deterministic validation prefers local tooling
- sensitive boundary work routes to human review or blocked policy
- low capacity produces warning
- local GPU decomposition suggestions are generated
- A2C profile labels are preserved as labels
- recommendation metadata does not schedule, dispatch, assign, or execute
- dispatch queue metadata integration if implemented
- Office summary generation if implemented
- no live provider/network/GPU calls are required

## Validation Recipe Requirement

If the Estate validation framework supports package-specific recipes, add a local validation recipe for this package.

At minimum, document or run:

```powershell
pytest -q tests/test_execution_routing.py
python -m estate.cli.main execution-routing-report
python -m estate.cli.main validation-production-readiness --json
```

Do not require live provider access.

## Acceptance Criteria

This package is complete when:

- recommendation request and result models exist
- deterministic recommendation rules are implemented
- local GPU is a first-class provider-fit option
- Codex CLI is not treated as the default implementation route
- task decomposition suggestions exist for local GPU-sized work
- recommendation metadata cannot itself schedule, dispatch, assign, or execute work
- dispatch queue can preserve recommendation metadata or a documented integration path exists
- Office of the Steward has a documented or minimal routing recommendation visibility path
- tests pass without live provider calls
- completion receipt exists if Codex executes the package

## Known Limitations To Preserve

Preserve these limitations unless separately resolved:

- This package does not measure real provider usage automatically.
- This package does not scrape Codex usage pages.
- This package does not run local Ollama/GPU tasks.
- This package does not implement final scheduling policy.
- This package does not replace future mechanical coordination layers.

## Completion Signal

If implemented by Codex, create:

```text
collaboration/work_packages/completions/WP-EXECUTION-PROVIDER-ROUTING-RECOMMENDATIONS-001_codex_done.json
```

The receipt must include files changed, tests run, recommendation examples, Office integration status, dispatch metadata integration status, known limitations, and skipped live-provider calls.
