# WP-EXECUTION-PROVIDER-ROUTING-001 - Execution Provider Routing and Local GPU Task Decomposition

Status: Proposed
Priority: High
Owner: Chief Architect / Steward
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Office of the Steward, Alfred, Helen, future Operations/Orchestrator, execution providers
Classification: Estate Internal
Created: 2026-07-08

## Codex Command

Read this work package and do exactly what it says.

Do not build the full orchestrator.

Do not dispatch live provider calls by default.

Do not assume Codex CLI is the default provider.

Do not ignore local GPU capacity.

Do not create a new Office.

## Mission

Implement the first execution-provider routing policy layer for The Estate.

The routing policy must help the Estate decide whether work should be routed to:

- Codex Cloud/Web
- Codex CLI
- ChatGPT / planning lane
- local Ollama / RTX 4090 GPU lane
- local deterministic tools such as PowerShell, Python, pytest, validation commands

The goal is not to make autonomous scheduling decisions yet. The goal is to attach explicit routing metadata and recommendation logic to dispatch work so the Steward and future Orchestrator can avoid wasting expensive provider capacity.

## Background

The Estate observed that Codex CLI can complete real implementation work, but may burn ChatGPT Business/Codex seat capacity very quickly when used for large local command-line implementation packages.

The Estate also has a local RTX 4090 capable of running local LLMs through Ollama. Local GPU execution should be used for smaller, bounded, low-risk subtasks where possible.

The refined operating principle is:

```text
Large conceptual or broad repo implementation work -> Codex Cloud/Web or ChatGPT planning lane
Local-runtime-required implementation -> Codex CLI only when justified
Small bounded decomposition/review/parsing/preflight tasks -> local Ollama / RTX 4090
Deterministic validation and file checks -> local tools
```

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

Implement a local routing policy module that supports:

1. A provider routing request model.
2. A provider routing recommendation model.
3. Rule-based recommendations for Cloud/Web, CLI, local GPU, ChatGPT planning, and deterministic tools.
4. Task decomposition recommendations for work that can be split into local-GPU-sized subtasks.
5. Capacity-aware fields for seat labels such as `A2C1`, `A2C2`, `A2C3`.
6. Local GPU capability fields for RTX 4090 / Ollama models.
7. Integration metadata for the Execution Dispatch Queue.
8. Current routing summary output for Office visibility.
9. Tests that do not require live Codex, ChatGPT, Ollama, or GPU execution.

## Out Of Scope

This package must not:

- execute live Codex or ChatGPT calls
- execute live Ollama/GPU calls as a required test path
- implement full autonomous scheduling
- implement multi-seat auto-rotation
- scrape browser usage pages
- create a new Office
- modify Alfred, Helen, or Ingrid authority
- store credentials, auth files, or browser profile data

## Routing Categories

Support these route labels at minimum:

```text
codex_cloud_web
codex_cli
chatgpt_planning
local_ollama_gpu
deterministic_local_tooling
human_review
blocked_needs_policy
```

## Routing Request Model

Create or support a routing request with fields such as:

```json
{
  "routing_id": "route_001",
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

## Routing Recommendation Model

Return recommendations with fields such as:

```json
{
  "routing_id": "route_001",
  "recommended_route": "local_ollama_gpu",
  "alternate_routes": ["codex_cloud_web"],
  "allowed_routes": ["local_ollama_gpu", "codex_cloud_web", "human_review"],
  "forbidden_routes": ["codex_cli"],
  "reason": "Small bounded implementation review can be decomposed for local GPU preflight before cloud execution.",
  "decomposition_recommended": true,
  "suggested_subtasks": [],
  "capacity_warning": false,
  "human_attention_required": false
}
```

## Routing Rules

Implement initial deterministic rules:

1. Broad conceptual planning should route to `chatgpt_planning` or `codex_cloud_web`.
2. Broad repo implementation should prefer `codex_cloud_web` over `codex_cli` unless local runtime is required.
3. Local runtime integration, Windows path behavior, local validation, local Ollama/GPU behavior, and A-drive-specific tasks may route to `codex_cli`.
4. Small bounded review, parsing, summarization, prompt cleanup, fixture generation, test-data generation, and decomposition tasks should prefer `local_ollama_gpu` when security allows.
5. Deterministic checks, validation commands, JSON/schema checks, file existence checks, and pytest runs should prefer `deterministic_local_tooling`.
6. Sensitive boundary questions should route to `human_review` or `blocked_needs_policy`.
7. If a seat/profile has low capacity, `codex_cli` and `codex_cloud_web` recommendations should include a capacity warning.

## Local GPU Decomposition

When a task is too large for local Ollama but contains smaller pieces, recommend decomposition.

Examples of GPU-sized subtasks:

- summarize one source file
- inspect one test file
- generate test cases for one module
- classify a work package by provider fit
- review a small diff
- extract acceptance criteria from one package
- draft a deterministic prompt from one package
- check whether a completion receipt is complete

The module should be able to produce a list of suggested subtasks without executing them.

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
docs/integration/execution_provider_routing_usage.md
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

If the Execution Dispatch Queue is present, add routing metadata fields or helper functions so a dispatch item can carry:

- recommended route
- allowed routes
- forbidden routes
- routing reason
- decomposition recommended
- suggested subtasks
- provider capacity warning

Do not break existing dispatch queue tests.

## Office Visibility

Generate a routing summary suitable for the Office of the Steward.

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
- local-runtime-required work may route to Codex CLI
- small bounded subtasks prefer local Ollama/GPU
- deterministic validation prefers local tooling
- sensitive boundary work routes to human review or blocked policy
- low capacity produces warning
- local GPU decomposition suggestions are generated
- A2C profile labels are preserved as labels
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

- routing request and recommendation models exist
- deterministic routing rules are implemented
- local GPU is a first-class route option
- Codex CLI is not treated as the default implementation route
- task decomposition suggestions exist for local GPU-sized work
- dispatch queue can preserve routing metadata or a documented integration path exists
- Office of the Steward has a documented or minimal routing visibility path
- tests pass without live provider calls
- completion receipt exists if Codex executes the package

## Known Limitations To Preserve

Preserve these limitations unless separately resolved:

- This package does not measure real provider usage automatically.
- This package does not scrape Codex usage pages.
- This package does not run local Ollama/GPU tasks.
- This package does not implement final scheduling policy.
- This package does not replace future Orchestrator design.

## Completion Signal

If implemented by Codex, create:

```text
collaboration/work_packages/completions/WP-EXECUTION-PROVIDER-ROUTING-001_codex_done.json
```

The receipt must include files changed, tests run, routing examples, Office integration status, dispatch integration status, known limitations, and skipped live-provider calls.
