# WP-0612 Operations / Execution Integration Audit

Status: completed with findings
Date: 2026-07-10
Classification: Estate Internal

## Audit result

The implemented chain is mostly coherent, but this repository now contains both the later provider-adapter packages (WP-0613+) and the requested WP-0600 through WP-0611 / CA5 execution surface. The accepted stack is visible as:

`Traffic Controller / Operations Manager -> Orchestrator Runtime Core -> Orchestrator Dispatch Record -> Execution Dispatch Queue / dispatch-to-adapter handoff -> Execution Provider Adapter Contract -> provider adapter -> provider runtime -> Execution Activity / validation -> Office visibility`.

The future adapter boundary is no longer purely future in this checkout: `execution-provider-adapter`, `codex-bridge-adapter`, and dispatch-to-adapter handoff code/docs already exist. The adapter contract is the right connection point between the provider-agnostic execution dispatch queue and provider-specific adapters. The Orchestrator should continue to stop at its own dispatch records and should not invoke providers.

## Explicit audit-question answers

1. **Are there duplicate operational event systems?** Yes, partially. The shared operations event feed uses `runtime/operations/events/`, while execution dispatch/activity and Codex Bridge also maintain provider-side JSONL feeds. They are compatible as scoped feeds but need a documented event-source hierarchy.
2. **Are there duplicate execution activity systems?** No direct duplicate; `execution_activity` is an aggregate surface over Codex Bridge and its own feed, not a competing dispatcher. Risk: Office command-center activity views can make it look like a second source of truth.
3. **Are there duplicate provider registries or catalogs?** Yes, there are adjacent planning-provider registry, provider catalog/capabilities, health/capacity, Codex Bridge identity policy, and provider-routing artifacts. They are not identical, but ownership should be consolidated.
4. **Are there duplicate dispatch queues?** Yes by design: Orchestrator dispatch records and the provider-agnostic execution dispatch queue both use dispatch language and queue/status artifacts. They are different stages and need an explicit bridge.
5. **Are Orchestrator dispatch records distinct from Execution Dispatch Queue records?** Yes. Orchestrator records are pre-provider handoff candidates with `pending_dispatch/blocked/deferred/cancelled`; execution dispatch records are provider-neutral execution intents with queued/running/completed lifecycle.
6. **Are CLI commands named consistently?** Mostly, but not completely. Orchestrator commands are flat (`orchestrator-cycle`, `orchestrator-dispatch-list`), execution dispatch is grouped (`execution-dispatch ...`), adapters are grouped, and provider catalog has legacy flat `providers-*` plus grouped `providers`.
7. **Are runtime artifact paths coherent?** Mostly. Major roots are coherent, but `runtime/operations/status`, `runtime/operations/control/status`, `runtime/orchestrator/*`, `runtime/execution_dispatch`, `runtime/execution_activity`, `runtime/execution_adapters`, and `runtime/codex_bridge` need a canonical chain diagram.
8. **Are Office panels reading compatible artifacts?** Yes. Office panels are read-only consumers of summaries/current snapshots. Missing artifacts degrade with warnings.
9. **Are validation receipts being produced consistently?** Partially. Work-package validation receipts exist under `runtime/validation/work_packages`; audit command can save `runtime/audit/latest.json`, but the Linux audit run exposed Windows `.estate.bat` assumptions in audit internals.
10. **Does Codex Bridge integrate as an execution provider adapter or is it coupled directly to orchestration?** In this checkout it integrates through `codex-bridge-adapter` and `execution-provider-adapter`; execution dispatch can prepare handoffs. It is not directly coupled to Orchestrator Runtime Core.
11. **Do provider health/capacity records connect to scheduling and assignment without duplication?** They connect to scheduler/runtime eligibility as evidence. Duplication risk remains because health and capacity have separate latest/summary artifacts.
12. **Does Worker Assignment Board preserve A2C labels without hardcoding seat limits?** Yes. A2C labels are assignment/profile labels and are not authority or fixed seat limits in reviewed docs/tests.
13. **Does Traffic Controller / Operations Manager remain distinct from Orchestrator?** Yes. Traffic Controller records posture/decisions; Orchestrator creates mechanical dispatch state.
14. **Does Orchestrator Runtime Core stop before provider execution?** Yes. Its docs and tests preserve a non-execution boundary.
15. **Where should the future Execution Provider Adapter Contract connect?** Between execution dispatch/handoff records and provider-specific adapters; Orchestrator dispatch records should first be normalized into execution dispatch or adapter request form.

## Runtime path inventory

| Path | Producer | Consumer | Package/source | Status | Conflict notes |
| --- | --- | --- | --- | --- | --- |
| `runtime/operations/events/` | operational event feed | Office activity, Orchestrator/Operations emitters | WP-0601 | implemented | overlaps conceptually with execution JSONL feeds |
| `runtime/operations/status/latest.json`, `active.json`, `recent.json`, `summary.md` | operational status summary | Office operational activity panel | WP-0601/0602 | implemented | canonical operations status feed |
| `runtime/orchestrator/intake/status/queue.json` | intake submit/decisions | scheduler, Office panel | WP-0603/0605 | implemented | no conflict |
| `runtime/orchestrator/schedule/status/queue.json` | scheduler | Orchestrator Runtime Core | WP-0606 | implemented | no conflict |
| `runtime/orchestrator/dispatch/status/queue.json` | Orchestrator Runtime Core | Traffic review, Office panel, future handoff | WP-0609 | implemented | dispatch naming overlaps execution dispatch |
| `runtime/execution_dispatch/queue.json` | execution dispatch CLI | adapter handoff, Office command center | WP-EXECUTION-DISPATCH-QUEUE-001 | implemented | needs explicit ingestion from Orchestrator dispatch |
| `runtime/execution_dispatch/events.jsonl` | execution dispatch queue | execution activity/report | CA5 execution dispatch | implemented | scoped execution event feed |
| `runtime/execution_activity/current.json` | execution activity surface | Office command center | WP-EXECUTION-ACTIVITY-SURFACE-001 | implemented | aggregate, not source of truth |
| `runtime/codex_bridge/current_status.json` and request folders | Codex Bridge | execution activity, Codex adapter | WP-CODEX-BRIDGE | implemented | provider-specific feed |
| `runtime/execution_adapters/requests/`, `results/`, `status/`, `reports/` | adapter contract/runtime | reconciliation, Office, validation | WP-0613+/WP-0504 | present | arrived after requested wave; confirms adapter seam |
| `runtime/providers/catalog_status.json` | provider catalog commands | scheduler/runtime/Office | WP-0604 | implemented | source-of-truth candidate for provider identity |
| `runtime/providers/health/status/summary.json` | provider health/capacity reporting | scheduler/runtime/Traffic | WP-0607 | implemented | health/capacity split should be documented |
| `runtime/workers/assignments/status/board.json` | worker assignment runtime | Orchestrator/Traffic/Office | WP-0608 | implemented | A2C labels preserved |
| `runtime/operations/control/status/summary.json` | Traffic Controller / Operations Manager | Office Traffic Controller panel | WP-0610/0611 | implemented | distinct from operations event status |
| `runtime/validation/work_packages/` | validation commands/manual receipts | auditors | governance | implemented | this package writes WP-0612 receipt |

## CLI command inventory

| Command | Purpose | Package/source | Runtime paths touched | Status | Conflict notes |
| --- | --- | --- | --- | --- | --- |
| `audit` | repository audit | core audit | `runtime/audit/latest.json` with `--save` | warning | Linux run failed internal `.estate.bat` checks |
| `operations-event-record` | append operational event | WP-0601 | `runtime/operations/events/` | implemented | shared operational feed |
| `operations-status-summary` | summarize operations status | WP-0601 | `runtime/operations/status/*` | implemented | source for activity panel |
| `planning-provider-run` | run planning-provider request | WP-0600 | planning provider artifacts/events | implemented | not provider execution |
| `orchestrator-intake-submit` | submit intake | WP-0603 | `runtime/orchestrator/intake/*` | implemented | no live execution |
| `orchestrator-intake-decide` | approve/block/defer intake | WP-0605 | intake decisions/status, operations events | implemented | command naming flat |
| `orchestrator-schedule` / `orchestrator-schedule-list` | schedule approved intake | WP-0606 | `runtime/orchestrator/schedule/*` | implemented | no provider execution |
| `orchestrator-cycle` | bounded runtime cycle | WP-0609 | runtime and orchestrator dispatch paths | implemented | stops at dispatch records |
| `orchestrator-dispatch-list` | list orchestrator dispatch | WP-0609 | `runtime/orchestrator/dispatch/status/queue.json` | implemented | distinct from execution-dispatch list |
| `providers-list/show/find` | provider catalog inspection | WP-0604 | catalog status | implemented | flat command family |
| `providers-health-set`, `providers-capacity-set`, `providers-health-summary` | health/capacity evidence | WP-0607 | `runtime/providers/health/*` | implemented | naming mixes health/capacity |
| `worker-assignment-record`, `worker-assignment-board` | assignment evidence/board | WP-0608 | `runtime/workers/assignments/*` | implemented | A2C label inventory |
| `operations-review`, `operations-decide`, `operations-decisions-list` | Traffic posture/decisions | WP-0610 | `runtime/operations/control/*` | implemented | distinct from Orchestrator |
| `office-traffic-controller-panel` | Office panel summary | WP-0611 | `runtime/operations/control/status/*` | implemented | read-only surface |
| `execution-activity`, `execution-activity-report` | execution activity aggregate | CA5 activity surface | `runtime/execution_activity/*` | implemented | read-only aggregate |
| `execution-dispatch ...` | provider-neutral queue | CA5 dispatch queue | `runtime/execution_dispatch/*` | implemented | duplicate dispatch terminology |
| `codex-bridge` | bounded Codex Bridge request | Codex Bridge | `runtime/codex_bridge/*` | implemented | provider-specific runtime |
| `codex-bridge-adapter validate/dry-run` | Codex behind adapter | WP-0504 | `runtime/execution_adapters/*` | present | correct adapter boundary |
| `execution-provider-adapter validate/dry-run` | provider-neutral adapter contract | WP-0613+ | `runtime/execution_adapters/*` | present | safe next only after handoff mapping repair |
| `execution-adapter-handoff prepare/validate` | dispatch-to-adapter handoff | post-wave integration | `runtime/execution_adapters/requests/*` | present | desired bridge between queues |

## Models/contracts inventory

| Model name | File path | Responsibility | Overlaps with | Recommended source of truth |
| --- | --- | --- | --- | --- |
| Planning provider request/response/events | `src/estate/core/planning_provider*.py` | planning-only provider framework | provider catalog | planning provider module for planning tasks only |
| Provider catalog/capabilities | `src/estate/core/provider_catalog.py`, `provider_capabilities.py` | provider identity/capability/classification | Codex Bridge provider IDs, routing | provider catalog should own identity/capability |
| ProviderHealth/ProviderCapacity | `src/estate/core/provider_health.py`, `provider_capacity.py` | availability/capacity evidence | scheduler/runtime eligibility | provider health/capacity status summaries |
| Orchestrator intake/decision/schedule | `src/estate/core/orchestrator_intake*.py`, `orchestrator_scheduler.py` | request approval and scheduling | operations decisions | Orchestrator intake/schedule for work readiness |
| DispatchRecord | `src/estate/core/orchestrator_dispatch.py` | pre-provider dispatch candidate | execution dispatch item | Orchestrator for pre-adapter state only |
| ExecutionDispatchItem | `src/estate/core/execution_dispatch.py` | provider-neutral execution queue item | Orchestrator DispatchRecord | execution dispatch for provider execution intent |
| ExecutionProviderAdapterRequest/Result | `src/estate/core/execution_provider_adapter.py` | provider-neutral adapter contract | Codex Bridge request/result | adapter contract for provider invocation boundary |
| CodexBridgeRequest/Result | `src/estate/core/codex_bridge.py` | Codex-specific local execution wrapper | adapter request | Codex Bridge only behind adapter |
| ExecutionActivitySnapshot/Event | `src/estate/core/execution_activity.py` | aggregate provider execution visibility | operational activity | execution activity for provider lifecycle visibility |
| OperationsReview/RecommendedAction | `src/estate/core/traffic_controller.py` | posture/recommendations | scheduler policy | Traffic Controller for movement posture |
| OperationsDecision | `src/estate/core/operations_manager.py` | durable operations decisions | intake decisions | Operations Manager for posture decisions only |
| WorkerAssignmentRecord/Board | `src/estate/core/worker_assignments.py`, `worker_assignment_runtime.py` | worker/A2C assignment evidence | provider capacity | assignment board for worker availability labels |

## Office surfaces inventory

| Surface/panel | Data source | Action controls | Status | Conflict notes |
| --- | --- | --- | --- | --- |
| Office operational activity panel | `runtime/operations/status/*` | none/read-only | implemented | reads shared event/status feed |
| Office Traffic Controller panel | `runtime/operations/control/status/*` | decision controls via operations manager | implemented | controls record decisions but do not execute providers |
| Office command center execution activity hook | `runtime/execution_activity/current.json` | none/read-only | implemented | aggregate only |
| Office command center execution dispatch hook | `runtime/execution_dispatch/current.json` | none/read-only | implemented | Office not dispatch authority |
| Provider routing office panel | `runtime/provider_routing/*` | recommendation only | present/read-only | out of scope for WP-0612; do not dispatch routing policy |
| Worker assignment board | `runtime/workers/assignments/status/board.json` | assignment record generation | implemented | preserves labels |

## Validation artifacts inventory

| Artifact | Package/source | Command run | Status | Notes |
| --- | --- | --- | --- | --- |
| `runtime/audit/latest.json` | audit core | `PYTHONPATH=src python -m estate.cli.main audit` | absent unless `--save`; command reported failures | audit output captured in this report |
| `runtime/validation/work_packages/WP-0612_validation.json` | WP-0612 | manual audit receipt | created | contains command/test summary |
| `operations/validation/reports/WP-0612_operations_execution_integration_audit.md` | WP-0612 | manual audit report | created | this report |
| `docs/architecture/operations_execution_integration_findings.md` | WP-0612 | summary findings | created | architecture recommendation |
| targeted pytest set | WP-0600..0611 + CA5 | `python -m pytest ... -q` | 155 passed, 4 failed without PYTHONPATH | failures were CLI subprocess env issue |
| provider catalog retest | WP-0604 | `PYTHONPATH=src python -m pytest tests/test_provider_catalog.py -q` | passed | 13 passed |

## Duplicate/conflict analysis

- **Duplicate/conflict count:** 5 material risks.
- **Risk 1:** operational feed vs execution/Codex feeds are separate JSONL event systems. Keep separate scopes, but document aggregation rules.
- **Risk 2:** Orchestrator dispatch and execution dispatch are two queues. Keep both, but add explicit conversion/handoff rules.
- **Risk 3:** provider identity appears in provider catalog, routing recommendations, Codex Bridge, and adapter profile policy. Provider catalog should be canonical.
- **Risk 4:** CLI naming is inconsistent between flat and grouped command families. Defer broad rename; document current names.
- **Risk 5:** validation/audit commands still assume Windows `.estate.bat` in Linux audit internals. Repair audit portability separately.

## Compatibility-chain analysis

Planning provider framework is separate from provider execution. Intake decisions and scheduler produce Orchestrator schedule records. Orchestrator Runtime Core consumes scheduled work and emits pre-provider dispatch records only. Execution Dispatch Queue is the provider-neutral execution-intent queue and should receive normalized dispatches from Orchestrator or a controlled handoff. Execution Provider Adapter Contract should consume adapter requests derived from execution dispatch/handoff records. Codex Bridge is correctly adapter-backed in the current checkout and should remain provider-specific. Execution Activity and Office panels remain read-only visibility layers.

## Recommended consolidation or repair packages

1. **Consolidation Repair:** define canonical handoff from `runtime/orchestrator/dispatch/*` to `runtime/execution_dispatch/queue.json` and adapter requests, including state mapping and event references.
2. **Provider Catalog Ownership Repair:** designate provider catalog as identity/capability source of truth; routing and Codex Bridge should reference it rather than define competing identities.
3. **Event Feed Hierarchy Repair:** document operations events as institutional movement events and execution activity/Codex feeds as provider lifecycle feeds aggregated upward.
4. **CLI Naming/Help Inventory:** document flat vs grouped command names and add aliases only in a later behavior package.
5. **Audit Portability Repair:** remove internal `.estate.bat` Linux failure mode or provide POSIX equivalent.

## Local commands and tests

- `git status --short`
- `./estate.bat audit` (failed on Linux: permission denied)
- `PYTHONPATH=src python -m estate.cli.main audit` (completed with 23 passed / 43 failed, mostly `.estate.bat` path assumptions and missing generated runtime/discovery artifacts)
- `python -m pytest tests/test_planning_provider.py tests/test_planning_provider_registry.py tests/test_planning_provider_runtime.py tests/test_office_operational_activity.py tests/test_orchestrator_intake.py tests/test_provider_capabilities.py tests/test_provider_catalog.py tests/test_orchestrator_intake_decisions.py tests/test_orchestrator_scheduler.py tests/test_provider_capacity.py tests/test_provider_health.py tests/test_worker_assignments.py tests/test_worker_assignment_runtime.py tests/test_orchestrator_runtime.py tests/test_orchestrator_dispatch.py tests/test_orchestrator_cycle.py tests/test_traffic_controller.py tests/test_operations_manager.py tests/test_office_traffic_controller_panel.py tests/test_codex_bridge.py tests/test_execution_activity.py tests/test_execution_dispatch.py -q` (155 passed, 4 failed; provider catalog CLI subprocesses lacked PYTHONPATH)
- `PYTHONPATH=src python -m pytest tests/test_provider_catalog.py -q` (13 passed)

## Next recommendation

Recommend **Consolidation Repair** before dispatching provider routing or policy work. The adapter contract is architecturally safe as the correct seam, but in this checkout it is already present; the next useful package should repair/document the Orchestrator-dispatch to Execution-dispatch/adapter handoff and canonical provider catalog ownership before adding routing policy.
