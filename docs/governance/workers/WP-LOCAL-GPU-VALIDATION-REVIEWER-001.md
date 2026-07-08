# WP-LOCAL-GPU-VALIDATION-REVIEWER-001 - Local GPU Validation Reviewer

Status: Proposed
Priority: High
Owner: Chief Architect / Steward
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Office of the Steward, Audit, Validation, Traffic Controller / Operations Manager, Chief Architects
Classification: Estate Internal
Created: 2026-07-08

## Codex Command

Read this work package and do exactly what it says.

Do not implement provider execution.

Do not repair implementation code unless explicitly assigned.

Do not require live cloud access.

Do not require Codex CLI, ChatGPT, OpenAI API, or network access.

Do not require live Ollama/GPU execution in unit tests.

Implement the local validation reviewer substrate so deterministic validation artifacts can be reviewed by local reasoning models on the RTX 4090 / Ollama lane.

## Mission

Implement a local validation reviewer that turns deterministic validation evidence into structured review recommendations.

The Estate operating model is:

```text
Cloud/Web implementation builds.
Local deterministic tools prove facts.
Local RTX 4090 / Ollama reviews validation meaning.
CLI premium local model escalates only when needed.
Chief Architect / Steward accepts institutional truth.
```

This package implements the local reviewer substrate for the third step.

## Background

The Estate has local RTX 4090 capacity and local Ollama models. Most package validation should not require premium Codex seat usage. Codex-produced implementations already include tests and validation recipes. The local machine can run deterministic commands, collect artifacts, and then use local reasoning to decide whether the evidence appears complete, coherent, in scope, and ready for human/Chief Architect review.

This package must create the structured local-review layer without requiring live model calls in tests.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/architecture/execution_provider_operational_visibility_requirements.md
docs/integration/execution_activity_surface_usage.md
docs/integration/execution_dispatch_queue_usage.md
docs/governance/workers/WP-EXECUTION-PROVIDER-ROUTING-RECOMMENDATIONS-001.md
```

If any file is missing locally, record it in the implementation report and continue with available canonical files.

## Scope

Implement a local GPU validation reviewer substrate that supports:

1. A validation review request model.
2. A validation review result model.
3. Deterministic evidence ingestion from existing validation artifacts.
4. Completion receipt review.
5. Scope and boundary checklist review.
6. Office visibility artifact checks.
7. Local reasoning provider abstraction, with a stub/mock provider for tests.
8. Ollama/RTX 4090 as a documented optional runtime provider.
9. Structured PASS / FAIL / BLOCKED / ESCALATE recommendation output.
10. Review artifacts written under runtime validation storage.
11. Office-readable summary output if clean and low-risk.

## Out Of Scope

This package must not:

- implement live cloud model calls
- require live Ollama/GPU calls in tests
- implement code repair
- implement provider dispatch
- replace deterministic validation commands
- replace Audit
- replace Chief Architect review
- replace Steward acceptance
- mark work institutionally complete by itself

## Review Request Model

Support a review request shape such as:

```json
{
  "review_id": "review_WP_EXAMPLE",
  "work_package_id": "WP-EXAMPLE",
  "work_package_path": "docs/governance/workers/WP-EXAMPLE.md",
  "validation_artifact_paths": [],
  "completion_receipt_path": "collaboration/work_packages/completions/WP-EXAMPLE_codex_done.json",
  "changed_files": [],
  "expected_artifacts": [],
  "classification": "Estate Internal",
  "local_reasoning_provider": "ollama_stub",
  "requires_model_review": true,
  "created_at": "2026-07-08T00:00:00Z"
}
```

## Review Result Model

Return a result shape such as:

```json
{
  "work_package_id": "WP-EXAMPLE",
  "deterministic_validation_status": "passed",
  "receipt_status": "complete",
  "scope_status": "in_scope",
  "boundary_status": "clean",
  "office_visibility_status": "present",
  "local_gpu_review": "pass",
  "recommendation": "ready_for_chief_architect_review",
  "evidence_paths": [],
  "concerns": [],
  "requires_escalation": false,
  "escalation_reason": null
}
```

Support recommendation values at minimum:

```text
ready_for_chief_architect_review
fail_requires_repair
blocked_missing_evidence
escalate_to_cli_validation
escalate_to_human_review
```

## Evidence Review Checks

The reviewer should inspect available artifacts and determine:

- whether package-specific tests passed
- whether validation recipe output exists
- whether production readiness is true when applicable
- whether completion receipt exists
- whether completion receipt appears complete
- whether expected implementation files exist
- whether expected docs exist
- whether runtime artifacts were generated where required
- whether Office visibility checks were performed where required
- whether skipped live-provider calls are documented
- whether work appears to have stayed in scope
- whether boundary warnings require escalation

## Local Reasoning Provider Abstraction

Implement a small abstraction for local reasoning review.

It should allow:

- stub reviewer for tests
- optional Ollama reviewer documentation
- deterministic fallback review when no model is available

Tests must use stub/fake providers only.

The package must not require Ollama to be running in CI or test mode.

## Runtime Paths

Use local runtime storage by default:

```text
runtime/validation/reviews/<work_package_id>_review.json
runtime/validation/reviews/<work_package_id>_review.md
runtime/validation/reviews/latest.json
```

Do not commit live runtime review outputs unless intentionally captured as evidence.

## Expected Artifacts

Create or update only paths justified by the existing codebase.

Expected implementation artifacts:

```text
src/estate/core/local_gpu_validation_reviewer.py
tests/test_local_gpu_validation_reviewer.py
docs/integration/local_gpu_validation_reviewer_usage.md
```

Likely integration touchpoints, if clean and low-risk:

```text
src/estate/cli/main.py
src/estate/core/steward_command_center.py
src/estate/core/operator_activity_stream.py
src/estate/core/work_package_validation.py
```

## CLI Requirements

If CLI wiring is straightforward, expose commands such as:

```text
python -m estate.cli.main local-gpu-validation-review --work-package WP-EXAMPLE --json
python -m estate.cli.main local-gpu-validation-review --request <request.json> --json
python -m estate.cli.main local-gpu-validation-review-report --work-package WP-EXAMPLE
```

If CLI wiring is not straightforward, implement documented Python entry points and defer full CLI wiring.

## Office Visibility

If the Office command center has a clear pattern, expose a validation review panel or status field showing:

- latest reviewed work package
- recommendation
- requires escalation
- deterministic validation status
- receipt status
- number of concerns
- evidence artifact path

Do not rewrite the Office UI.

## Test Requirements

Tests must cover:

- review request parsing
- review result generation
- passed deterministic validation produces ready recommendation
- missing completion receipt produces blocked recommendation
- failed validation produces repair recommendation
- boundary warning produces escalation recommendation
- stub local reasoning provider can add concern text
- review artifacts are written to runtime validation review paths
- human-readable review report is generated
- no live Ollama/GPU/cloud/network calls are required
- Office summary generation if implemented

## Validation Recipe Requirement

If the Estate validation framework supports package-specific recipes, add a local validation recipe for this package.

At minimum, document or run:

```powershell
pytest -q tests/test_local_gpu_validation_reviewer.py
python -m estate.cli.main local-gpu-validation-review --work-package WP-EXAMPLE --json
python -m estate.cli.main validation-production-readiness --json
```

Do not require live provider access.

## Acceptance Criteria

This package is complete when:

- local validation review request and result models exist
- deterministic validation artifacts can be inspected
- completion receipts can be reviewed
- a local reasoning provider abstraction exists
- tests use only fake/stub reasoning providers
- review JSON and Markdown artifacts are generated
- recommendation values include ready, repair, blocked, and escalation states
- local RTX 4090 / Ollama usage is documented as optional runtime behavior
- Office visibility is documented or minimally integrated
- tests pass without live provider calls
- completion receipt exists if Codex executes the package

## Known Limitations To Preserve

Preserve these limitations unless separately resolved:

- This package does not prove semantic correctness alone.
- This package does not replace deterministic tests.
- This package does not replace Audit or Chief Architect review.
- This package does not perform repairs.
- This package does not require live Ollama during tests.

## Completion Signal

If implemented by Codex, create:

```text
collaboration/work_packages/completions/WP-LOCAL-GPU-VALIDATION-REVIEWER-001_codex_done.json
```

The receipt must include files changed, tests run, review examples, Office integration status, known limitations, and skipped live-provider calls.
