# WP-0501 - Execution Provider Boundary Review After Background Operations Merge Wave

Status: Proposed
Priority: High
Owner: Chief Architect #5
Boundary Authority: Ingrid / Privacy and Boundary Office
Primary Consumers: Chief Architect, Traffic Controller / Operations Manager, Background Operations, Audit / Validation, Office of the Steward
Classification: Estate Internal
Created: 2026-07-09

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository review, boundary verification, documentation, and deterministic validation work. It does not require local GPU access, live provider execution, Codex CLI capacity, or network-dependent tests.
```

Local runtime required:

```text
false
```

Local runtime requirement details:

```text
Repository-level inspection and deterministic tests should be sufficient for baseline completion. Local validation and Ring 2 review may be performed after merge if the Steward wants additional evidence.
```

Capacity note:

```text
Use Codex Cloud/Web. Do not use Codex CLI unless repository behavior cannot be understood from the available files or local runtime evidence contradicts repository artifacts.
```

## Codex Command

```text
Read this work package and do exactly what it says.

Do not exceed the stated scope.

Do not create new offices, registries, providers, event systems, or command surfaces unless explicitly required.

Do not perform live provider calls.

Do not schedule work, dispatch work, assign workers, execute providers, approve institutional truth, or modify governance.

Preserve the distinction between CA5 execution-provider ownership and CA6 Background Operations ownership.
```

## Mission

Perform a Chief Architect #5 execution-provider boundary review after the recent merged work affecting provider recommendations, Office provider-routing visibility, Background Operations, post-merge audit, operational targets, and operations runtime service loops.

This package must verify that the merged work preserves the Estate's execution-provider boundaries.

The purpose is not to take ownership of CA6 Background Operations work.

The purpose is to confirm that the CA5 execution-provider lane remains clean, advisory where appropriate, and free from accidental routing authority, provider execution authority, dispatch authority, or autonomous movement authority.

## Background

Chief Architect #5 owns the execution-provider architecture lane.

Relevant CA5 execution-provider foundation includes:

```text
Codex Bridge
Execution Activity Surface
Execution Dispatch Queue
Execution Provider Adapter Contract
Provider Routing Recommendations
Provider Routing Office Visibility
```

Recent merged work in adjacent streams added or expanded:

```text
WP-0614 - Provider Routing Recommendations
WP-0615 - Office Provider Routing Recommendations Panel
WP-0617 - Background Operations Event Runtime
WP-0618 - Operational Targets and Post-Merge Audit
WP-0619 - Operations Runtime Service Loop
```

The 061x packages are not CA5-owned package numbers.

CA5 may review their impact on execution-provider seams, but CA5 must not assume ownership of the 600-series Background Operations lane.

This package exists because the merge wave materially affects the boundary between provider recommendation, provider execution, dispatch, background observation, validation/audit, Office visibility, and Steward acceptance.

## Institutional Boundary

The accepted Estate boundary remains:

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
A recommendation is evidence for a decision.
A validation result is evidence for acceptance.
A background operation may observe and request.
None of these are autonomous authority.
```

## Scope

This package must review and document whether the recent merge wave preserves these boundaries:

1. Provider routing recommendations remain advisory only.
2. Office provider-routing panels remain visibility surfaces only.
3. Background Operations does not become an execution provider.
4. Background Operations does not dispatch work.
5. Background Operations does not assign workers.
6. Background Operations does not perform provider execution.
7. Background Operations does not become routing authority.
8. Post-merge audit creates evidence but does not accept institutional truth.
9. Validation workflows remain deterministic unless explicitly marked otherwise.
10. Provider Adapter Contract remains the handoff seam for provider execution.
11. Execution Dispatch Queue remains the queue of candidate work, not replaced by Background Operations.
12. No duplicate provider registry, dispatch queue, event feed, or office has been introduced in the CA5 lane.
13. Runtime and Office surfaces distinguish advisory, validation, audit, and acceptance states.
14. Local validation evidence does not need to be committed merely because validation was run.
15. Transient validation evidence should be compatible with a future external validation evidence root.

## Out Of Scope

This package must not:

- implement new provider routing policy;
- schedule work;
- dispatch work;
- assign workers;
- execute providers;
- call Codex CLI;
- call ChatGPT CLI;
- call Ollama;
- call live network services;
- modify Background Operations ownership;
- modify Traffic Controller / Operations Manager authority;
- modify Orchestrator runtime authority;
- create a new provider catalog;
- create a new dispatch queue;
- create a new event system;
- create a new office;
- rename or renumber existing 600-series packages;
- take ownership of CA6 Background Operations work.

## Required Reading

Before review, read:

```text
AI_START_HERE.md
AI_HINTS.md
docs/governance/Estate_Manual.md
docs/governance/workers/templates/Codex_Work_Package_Template_v1.md
docs/integration/execution_provider_adapter_contract.md
docs/integration/provider_routing_recommendations.md
docs/integration/provider_routing_office_panel.md
docs/integration/background_operations_event_runtime.md
docs/integration/background_operational_targets_and_post_merge_audit.md
docs/integration/operations_runtime_service_loop.md
collaboration/work_packages/completions/WP-0614_codex_done.json
collaboration/work_packages/completions/WP-0615_codex_done.json
collaboration/work_packages/completions/WP-0617_codex_done.json
collaboration/work_packages/completions/WP-0618_codex_done.json
collaboration/work_packages/completions/WP-0619_codex_done.json
```

If any file is missing, record the missing file and continue with available canonical artifacts.

## Expected Artifacts

Create:

```text
docs/architecture/execution_provider_boundary_review_after_background_operations_merge_wave.md
```

Create:

```text
operations/validation/reports/WP-0501_execution_provider_boundary_review.md
```

Create:

```text
collaboration/work_packages/completions/WP-0501_codex_done.json
```

If consistent with existing validation conventions, add a deterministic validation recipe for WP-0501 in:

```text
src/estate/core/work_package_validation.py
```

If adding a validation recipe is too broad or conflicts with current validation architecture, document the reason instead of forcing it.

## Review Requirements

The architecture report must include:

1. Executive verdict.
2. Files reviewed.
3. Relevant merged packages.
4. Execution-provider boundary map.
5. Background Operations boundary map.
6. Provider recommendation boundary check.
7. Provider Office panel boundary check.
8. Dispatch Queue non-overlap check.
9. Provider Adapter Contract non-overlap check.
10. Audit / Validation / Acceptance separation check.
11. Runtime artifact and Office visibility check.
12. Duplicate-system risk check.
13. Any findings.
14. Required follow-up packages, if any.
15. CA5 recommendation to Chief Architect / Steward.

## Deterministic Checks

Where practical, add tests or validation checks that verify:

```text
provider routing recommendation artifacts do not schedule work
provider routing recommendation artifacts do not dispatch work
provider routing recommendation artifacts do not execute providers
provider routing Office panel artifacts are advisory / visibility only
background operations artifacts do not call provider adapters for live execution
post-merge audit artifacts produce evidence, not acceptance
operations runtime service loop does not become autonomous approval authority
completion receipt records no live provider calls
```

Do not add brittle tests that simply search every repository file for broad words like "dispatch" or "execute." Checks should be targeted to the relevant modules and documents.

## Validation Expectations

Run deterministic validation where available.

Likely commands:

```text
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0614 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0615 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0617 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0618 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0619 --json
```

If WP-0501 validation recipe is added, also run:

```text
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0501 --json
```

Run focused deterministic tests relevant to reviewed surfaces where available:

```text
pytest -q tests/test_provider_routing_recommendations.py tests/test_provider_routing_recommendations_runtime.py tests/test_provider_routing_office_panel.py
pytest -q tests/test_background_operations.py tests/test_background_operations_runtime.py
pytest -q tests/test_operational_targets.py tests/test_operational_targets_runtime.py tests/test_post_merge_audit.py tests/test_post_merge_audit_runtime.py
pytest -q tests/test_operations_runtime.py tests/test_operations_runtime_service.py
```

Adjust exact command paths to match repository state.

## Completion Receipt Requirements

The completion receipt must include:

```text
work_package_id
status
owner
files_reviewed
files_created
validation_commands_run
validation_results
findings
boundary_verdicts
live_provider_calls_made
dispatch_behavior_modified
provider_adapter_behavior_modified
background_operations_behavior_modified
office_surface_behavior_modified
known_limitations
ready_for_ca_review
```

The receipt must explicitly state:

```text
live_provider_calls_made: false
```

The receipt must also state whether any implementation files were modified. If this package only produces review artifacts and validation recipe support, say so clearly.

## Acceptance Criteria

This package is complete when:

1. A CA5 boundary review document exists.
2. A validation/report artifact exists.
3. The report clearly distinguishes CA5 execution-provider ownership from CA6 Background Operations ownership.
4. The report states whether WP-0614/WP-0615 remained advisory and visibility-only.
5. The report states whether WP-0617/WP-0618/WP-0619 preserved the no-provider-execution and no-dispatch-authority boundaries.
6. Any findings are listed as follow-up packages rather than silently repaired out of scope.
7. Completion receipt exists.
8. Deterministic validation was run or unavailable validation was documented.
9. No live provider calls were required.
10. No autonomous execution, routing, dispatch, assignment, or acceptance authority was introduced by this package.

## Steward / Chief Architect Note

This is a CA5 500-series package.

It reviews execution-provider boundary integrity after adjacent 600-series Background Operations work, but it does not take ownership of the 600-series lane.

CA5 owns the execution-provider seam.

CA6 owns Background Operations.

This package exists to keep those seams clean as the Estate becomes more operationally alive.
