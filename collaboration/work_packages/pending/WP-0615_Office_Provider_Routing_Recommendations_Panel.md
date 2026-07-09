# WP-0615 - Office Provider Routing Recommendations Panel

Status: Proposed  
Priority: High  
Owner: Chief Architect  
Boundary Authority: Ingrid / Privacy and Boundary Office  
Primary Consumers: Office of the Steward, Traffic Controller / Operations Manager, Execution Provider Adapter Contract, Provider Routing Recommendations  
Classification: Estate Internal  
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository implementation work for an Office-facing status/control surface. It should not require local Codex CLI, live provider calls, local GPU access, or network access. Codex Cloud/Web is appropriate when capacity is available.
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
Do not use Codex CLI capacity for implementation unless Cloud/Web cannot complete the package. Use local PowerShell/Python for deterministic validation and local RTX 4090/Ollama for Ring 2 review.
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

Add an Office-facing panel/status surface for WP-0614 provider routing recommendations.

The Office of the Steward and Traffic Controller / Operations Manager need to see provider-fit recommendation evidence before deciding movement. This package must surface recommendation metadata, rationale, alternatives, capacity notes, validation rings, boundary-review flags, and stale/missing artifact states.

This package must not make routing recommendations autonomous. It must not schedule, dispatch, assign, or execute work.

## Background

WP-0614 implemented provider routing recommendations as advisory metadata only. Recommendations can identify likely fit among deterministic local tooling, local RTX 4090/Ollama, ChatGPT planning, Codex Cloud/Web, Codex CLI, and human review.

The accepted boundary remains:

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

This package consumes recommendation artifacts and makes them visible. It does not create a new routing engine.

## Required Reading

Before implementation, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/workers/templates/Codex_Work_Package_Template_v1.md
docs/integration/provider_routing_recommendations.md
docs/integration/execution_provider_adapter_contract.md
collaboration/work_packages/pending/WP-0614_Execution_Provider_Routing_Recommendations.md
collaboration/work_packages/pending/WP-0613_Execution_Provider_Adapter_Contract.md
```

If any file is missing locally, record it and continue with available canonical files.

## Scope

This package must implement:

1. Office-readable provider routing recommendation summary loader.
2. Office panel payload for latest recommendations.
3. Traffic Controller friendly recommendation status fields.
4. Stale, missing, malformed, and empty-state handling.
5. Classification-aware safe summaries.
6. Explicit advisory-only labeling in Office payload.
7. Provider capacity and local-runtime warning display fields.
8. Alternative provider display fields.
9. Boundary/human-review required display fields.
10. Deterministic tests and integration documentation.

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
- create a new provider catalog,
- create a new dispatch queue,
- create a new event system,
- create a new office,
- make recommendations into decisions.

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
The Office panel displays advisory recommendation evidence. It must not approve, schedule, dispatch, assign, or execute work. If existing Office/Traffic Controller controls support related decisions, this package may link to them only as existing controls and must not invent unsupported actions.
```

## Expected Artifacts

Expected implementation artifacts:

```text
src/estate/core/provider_routing_office_panel.py
tests/test_provider_routing_office_panel.py
docs/integration/provider_routing_office_panel.md
```

Optional integration touchpoints, if clean and low-risk:

```text
src/estate/core/steward_command_center.py
src/estate/cli/main.py
src/estate/core/provider_routing_recommendations_runtime.py
```

Do not create duplicate provider catalog, recommendation engine, dispatch queue, event feed, or Office command system.

## Runtime Artifacts

The panel should read existing WP-0614 runtime artifacts such as:

```text
runtime/provider_routing/recommendations/<recommendation_id>.json
runtime/provider_routing/status/latest.json
runtime/provider_routing/status/summary.json
runtime/provider_routing/reports/<recommendation_id>.md
```

If a panel summary artifact is needed, use:

```text
runtime/provider_routing/office_panel/latest.json
runtime/provider_routing/office_panel/summary.json
```

Do not commit live runtime outputs unless explicitly required as evidence.

## Panel Requirements

Panel payload should include:

```text
available
stale
advisory_only
latest_recommendation_id
recommended_provider
alternate_providers
provider_rationale
capacity_note
local_runtime_required
human_review_required
boundary_review_required
validation_rings_required
not_recommended
source_artifact
work_package_id
classification
safe_summary
warnings
errors
updated_at
```

The payload must clearly state that recommendation output is not a movement decision.

## Test Requirements

Tests must cover:

- latest recommendation appears in Office panel payload,
- advisory_only is always true,
- missing artifacts produce unavailable panel state,
- malformed artifacts produce safe error state,
- stale artifacts are marked stale,
- classification-sensitive fields are summarized safely,
- capacity note appears,
- local runtime warning appears when relevant,
- human review and boundary review flags appear,
- no scheduling, dispatch, assignment, provider execution, or live calls occur,
- no duplicate routing engine is introduced.

## Validation Rings

### Ring 0 - Static / Structural Validation

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\provider_routing_office_panel.py
Test-Path tests\test_provider_routing_office_panel.py
Test-Path docs\integration\provider_routing_office_panel.md
python -m py_compile src\estate\core\provider_routing_office_panel.py
```

### Ring 1 - Deterministic Test Validation

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_provider_routing_office_panel.py --basetemp Temp/pytest-provider-routing-office-panel
python -m estate.cli.main validate-work-package --id WP-0615 --json
```

Expected evidence:

```text
runtime/validation/work_packages/WP-0615_validation.json
operations/validation/reports/WP-0615_validation.md
collaboration/work_packages/completions/WP-0615_codex_done.json
```

### Ring 2 - Local GPU Reasoning Review

Reviewer questions:

```text
Did the panel keep routing recommendations advisory only?
Did it avoid scheduling, dispatch, assignment, and execution?
Did it avoid creating duplicate provider catalogs, dispatch queues, event systems, command surfaces, or offices?
Did it surface provider capacity and local runtime guidance clearly?
Did it preserve Traffic Controller / Operations Manager as the movement decision layer?
Did deterministic validation pass?
Is this ready for Chief Architect review?
```

Expected commands when available:

```powershell
Clear-Host
cd A:\theestate
python -m estate.cli.main local-gpu-validation-review --work-package WP-0615 --json
python -m estate.cli.main local-gpu-validation-review-report --work-package WP-0615
```

Expected evidence:

```text
runtime/validation/reviews/WP-0615_review.json
runtime/validation/reviews/WP-0615_review.md
```

### Ring 3 - CLI Escalation Validation

Use only when Ring 1 and Ring 2 are insufficient. Prefer read-only validation. Do not repair code unless explicitly assigned.

### Ring 4 - Institutional Acceptance

Chief Architect / Steward acceptance must confirm validation evidence, local review recommendation, unresolved concerns, and promotion or repair decision.

## Completion Receipt Requirements

If implemented by Codex or another provider, create:

```text
collaboration/work_packages/completions/WP-0615_codex_done.json
```

The receipt must include work_package_id, provider, files changed, tests run, validation commands run, runtime artifacts generated, docs updated, Office integration status, skipped live-provider calls, known limitations, and follow-up recommendations.

## Promotion Criteria

This package is ready for promotion when Ring 0 passes, Ring 1 passes, Ring 2 recommends Chief Architect review, Ring 3 is not required or completed, completion receipt is present, no blocking boundary issue remains, and Chief Architect / Steward acceptance is recorded.

## Completion Signal

If implemented by Codex, create the completion receipt and include validation ring evidence paths.
