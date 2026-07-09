# WP-0612 Operations / Execution Integration Audit

Status: Completed with findings
Work package: WP-0612
Classification: Estate Internal
Started: 2026-07-09T00:00:00Z
Completed: 2026-07-09T00:00:00Z

## Executive Result

The implemented chain is mostly coherent from planning/intake through Orchestrator dispatch and Office visibility, but it is **not yet safe to dispatch the Execution Provider Adapter Contract as the next package without a consolidation repair first**. The audit found duplicate-but-separable provider catalogs, duplicate-but-separable dispatch queues, and multiple event/activity surfaces whose boundaries are not formally documented in one contract. No provider execution behavior was added by this audit.

Recommended next work package: **Consolidation Repair**.

## Accepted Chain Assessment

Accepted target chain:

```text
Traffic Controller / Operations Manager
  -> Orchestrator Runtime Core
  -> Dispatch Record
  -> Execution Provider Adapter Contract
  -> Provider Adapter
  -> Execution Provider
  -> Audit / Validation
  -> Office Visibility
```

Implemented chain today:

```text
Planning Provider / Work Package
  -> Orchestrator Intake
  -> Intake Decision Controls
  -> Scheduling Skeleton
  -> Orchestrator Runtime Cycle
  -> Orchestrator Dispatch Record
  -> [future Execution Provider Adapter Contract boundary]
  -> Execution Dispatch Queue / Codex Bridge handoff surface
  -> Codex Bridge dry-run/live adapter shell when explicitly invoked
  -> Execution Activity Surface
  -> Operations Status / Office panels
```

The Orchestrator Runtime Core stops at provider-agnostic dispatch record creation. The Execution Dispatch Queue is a lower-level provider-adapter queue that can prepare Codex Bridge handoffs, but no existing Orchestrator code automatically routes or enqueues Orchestrator dispatch records into that queue.

## Audit Questions

| # | Question | Answer |
| --- | --- | --- |
| 1 | Are there duplicate operational event systems? | **Partial duplication / boundary risk.** `runtime/operations/status/*` is the shared operational event/status system. Codex Bridge and execution activity also maintain event streams under `runtime/codex_bridge/*/events.jsonl`, `runtime/codex_bridge/events.jsonl`, and `runtime/execution_activity/events.jsonl`. These are execution-provider lifecycle feeds, not exact replacements, but the naming can confuse consumers. |
| 2 | Are there duplicate execution activity systems? | **No exact duplicate, but two related sources.** Execution Activity normalizes its own stream plus Codex Bridge current/status sources. Office operational activity reads operations status, not execution activity. |
| 3 | Are there duplicate provider registries or catalogs? | **Yes.** Legacy `data/registry/providers.json` coexists with operational `config/providers/catalog.json`. The operational stack uses the latter for provider descriptors/capability discovery; legacy service registry remains separate. |
| 4 | Are there duplicate dispatch queues? | **Yes, by layer.** `runtime/orchestrator/dispatch/status/queue.json` stores Orchestrator dispatch records, while `runtime/execution_dispatch/queue.json` stores provider-adapter dispatch items. They are distinct but need an adapter-boundary mapping contract. |
| 5 | Are Orchestrator dispatch records distinct from Execution Dispatch Queue records? | **Yes.** Orchestrator dispatch records are planning/scheduling outputs. Execution Dispatch items include adapter execution fields such as sandbox, allowed paths, provider profile, handoff reference, and terminal states. |
| 6 | Are CLI commands named consistently? | **Mostly, with historical inconsistency.** CA6 commands use `orchestrator-*`, `providers-*`, `worker-assignment-*`, `operations-*`; CA5 execution commands use `execution-dispatch` and `execution-activity`. There is also a legacy top-level `providers` command unrelated to `providers-list`. |
| 7 | Are runtime artifact paths coherent? | **Mostly.** CA6 paths cluster under `runtime/orchestrator`, `runtime/operations`, `runtime/providers`, and `runtime/workers`; CA5 paths cluster under `runtime/execution_dispatch`, `runtime/execution_activity`, and `runtime/codex_bridge`. The cross-cluster bridge is not formalized. |
| 8 | Are Office panels reading compatible artifacts? | **Yes for current panels.** Operational Activity reads `runtime/operations/status/*`; Traffic Controller panel reads `runtime/operations/control/*`; execution activity has CLI/report artifacts but no audited Office panel. |
| 9 | Are validation receipts being produced consistently? | **Partially.** Historical validation JSON/MD pairs exist under `runtime/validation/work_packages` and `operations/validation/reports`. WP-0612 follows that convention. Some execution-provider packages have completion receipts but not all have validation JSON receipts in the same path. |
| 10 | Does Codex Bridge integrate as an execution provider adapter or is it coupled directly to orchestration? | **Adapter-like and not directly coupled.** Codex Bridge is invoked through its CLI/core and by Execution Dispatch `prepare-handoff`; Orchestrator does not call it directly. This is the right boundary direction. |
| 11 | Do provider health/capacity records connect to scheduling and assignment without duplication? | **Partially.** Scheduling consults provider catalog availability; health/capacity summary is visible to Operations review. There is no single scheduling contract that consumes capacity as authoritative. |
| 12 | Does Worker Assignment Board preserve A2C labels without hardcoding seat limits? | **Yes.** Assignment records preserve `assignment_label`, `worker_id`, `provider_id`, `seat_id`, and profile metadata without observed hardcoded seat limits. |
| 13 | Does Traffic Controller / Operations Manager remain distinct from Orchestrator? | **Yes.** Operations review/decisions inspect queues and record control decisions; they do not perform Orchestrator scheduling or dispatch execution. |
| 14 | Does Orchestrator Runtime Core stop before provider execution? | **Yes.** Orchestrator cycle creates dispatch records and operational events only. |
| 15 | Where should the future Execution Provider Adapter Contract connect? | **Between `runtime/orchestrator/dispatch/status/queue.json` dispatch records and `runtime/execution_dispatch/queue.json` provider-adapter dispatch items.** It should transform an Orchestrator dispatch record into a provider-specific adapter request without embedding provider execution in Orchestrator. |

## Runtime Paths Inventory

| Path | Producer | Consumer | Package/source | Status | Conflict notes |
| --- | --- | --- | --- | --- | --- |
| `runtime/planning_provider/requests/*.json` | Planning provider runtime | Planning/provider tests, audit | WP-0600 | Active | Upstream planning artifact, no conflict. |
| `runtime/planning_provider/results/*.json` | Planning provider runtime | Intake/manual consumers | WP-0600 | Active | No automatic Orchestrator bridge audited. |
| `runtime/planning_provider/events/*.jsonl` | Planning provider runtime | Audit/status readers | WP-0600 | Active | Separate from operations status events. |
| `runtime/planning_provider/status/latest.json` | Planning provider runtime | CLI/status | WP-0600 | Active | Coherent. |
| `runtime/operations/status/active.json` | Operational status writer | Office Operational Activity | WP-0601/WP-0602 | Active | Shared lifecycle status source. |
| `runtime/operations/status/recent.json` | Operational status writer | Office Operational Activity | WP-0601/WP-0602 | Active | Shared lifecycle status source. |
| `runtime/operations/status/latest.json` | Operational status writer | Office Operational Activity | WP-0601/WP-0602 | Active | Shared lifecycle status source. |
| `runtime/operations/status/summary.md` | Operational status writer | Office Operational Activity | WP-0601/WP-0602 | Active | Human-readable status. |
| `runtime/orchestrator/intake/records/*.json` | Intake runtime | Scheduler | WP-0603 | Active | Intake source of truth. |
| `runtime/orchestrator/intake/status/queue.json` | Intake runtime | Scheduler, Operations review | WP-0603 | Active | Queue is intake-only, not dispatch. |
| `runtime/orchestrator/intake/status/latest.json` | Intake runtime | CLI/status | WP-0603 | Active | Coherent. |
| `runtime/orchestrator/schedule/records/*.json` | Schedule runtime | Orchestrator cycle | WP-0606 | Active | Schedule source of truth. |
| `runtime/orchestrator/schedule/status/queue.json` | Schedule runtime | Orchestrator cycle, Operations review | WP-0606 | Active | Queue is schedule-only. |
| `runtime/orchestrator/dispatch/records/*.json` | Orchestrator cycle | Future adapter contract, Operations review | WP-0609 | Active | Must not be confused with execution dispatch. |
| `runtime/orchestrator/dispatch/status/queue.json` | Orchestrator cycle | CLI/list, Operations review | WP-0609 | Active | Needs adapter mapping to execution dispatch. |
| `runtime/orchestrator/runtime/status/summary.md` | Orchestrator cycle | CLI/status | WP-0609 | Active | Runtime summary only. |
| `config/providers/catalog.json` | Provider catalog package/manual config | Provider catalog, scheduler, provider health | WP-0604/WP-0607 | Active | Operational provider source of truth candidate. |
| `runtime/providers/catalog/status.json` | Provider catalog writer | Office/status | WP-0604 | Active | Derived from `config/providers/catalog.json`. |
| `runtime/providers/health/records/*.json` | Provider health/capacity CLIs | Provider health summary, Operations review | WP-0607 | Active | Health and capacity share records dir. |
| `runtime/providers/health/status/latest.json` | Provider health writer | Provider health summary | WP-0607 | Active | Health latest by provider. |
| `runtime/providers/health/status/latest_capacity.json` | Provider capacity writer | Provider health summary | WP-0607 | Active | Capacity latest by provider. |
| `runtime/providers/health/status/summary.json` | Health/capacity writers | Operations review | WP-0607 | Active | Scheduling does not yet consume as formal policy. |
| `runtime/workers/assignments/records/*.json` | Worker assignment runtime | Assignment board, Operations review | WP-0608 | Active | Preserves A2C labels. |
| `runtime/workers/assignments/status/board.json` | Worker assignment runtime | Office/Operations review | WP-0608 | Active | No hard seat limit observed. |
| `runtime/operations/control/reviews/*.json` | Operations control runtime | Traffic Controller panel | WP-0610/WP-0611 | Active | Distinct from Orchestrator. |
| `runtime/operations/control/decisions/*.json` | Operations Manager decisions | Traffic Controller panel, events | WP-0610/WP-0611 | Active | Control decisions only; no dispatch execution. |
| `runtime/operations/control/status/latest.json` | Operations control runtime | Office Traffic Controller panel | WP-0610/WP-0611 | Active | Coherent. |
| `runtime/operations/control/status/summary.json` | Operations control runtime | Office Traffic Controller panel | WP-0610/WP-0611 | Active | Coherent. |
| `runtime/execution_dispatch/queue.json` | Execution dispatch queue | Execution Dispatch CLI, future adapters | WP-EXECUTION-DISPATCH-QUEUE-001 | Active | Duplicate dispatch queue by layer; needs formal bridge. |
| `runtime/execution_dispatch/events.jsonl` | Execution dispatch queue | Execution dispatch report/activity | WP-EXECUTION-DISPATCH-QUEUE-001 | Active | Execution event stream, not operations status. |
| `runtime/execution_dispatch/current.json` | Execution dispatch report | Office/CLI visibility | WP-EXECUTION-DISPATCH-QUEUE-001 | Active | Provider-adapter queue snapshot. |
| `runtime/execution_dispatch/handoffs/*.json` | Execution dispatch queue | Codex Bridge | WP-EXECUTION-DISPATCH-QUEUE-001 | Active | Correct adapter-handoff location. |
| `runtime/execution_activity/events.jsonl` | Execution activity writer | Execution activity report | WP-EXECUTION-ACTIVITY-SURFACE-001 | Active | Normalized execution activity, separate from operations status. |
| `runtime/execution_activity/current.json` | Execution activity writer | Execution activity report | WP-EXECUTION-ACTIVITY-SURFACE-001 | Active | No Office panel audited. |
| `runtime/codex_bridge/<request_id>/events.jsonl` | Codex Bridge | Execution activity surface | WP-CODEX-BRIDGE-IMPLEMENTATION | Active | Provider adapter lifecycle events. |
| `runtime/codex_bridge/<request_id>/status.json` | Codex Bridge | Execution activity surface | WP-CODEX-BRIDGE-IMPLEMENTATION | Active | Provider adapter status. |
| `runtime/codex_bridge/<request_id>/audit.json` | Codex Bridge | Audit/validation | WP-CODEX-BRIDGE-IMPLEMENTATION | Active | Provider execution audit artifact. |
| `runtime/codex_bridge/current_status.json` | Codex Bridge | Execution activity surface | WP-CODEX-BRIDGE-IMPLEMENTATION | Active | Latest provider adapter status. |
| `runtime/validation/work_packages/*.json` | Validation packages | Validation dashboards/auditors | Validation convention | Active | WP-0612 adds receipt here. |
| `operations/validation/reports/*.md` | Validation packages | Human audit readers | Validation convention | Active | WP-0612 adds report here. |

Runtime paths inventoried: 40.

## CLI Command Inventory

| Command | Purpose | Package/source | Runtime paths touched | Status | Conflict notes |
| --- | --- | --- | --- | --- | --- |
| `audit` | Run broad local audit | Legacy validation | Many audit paths | Attempted; failed in Linux due `.estate.bat` command assumptions | Windows wrapper convention conflicts with Linux shell. |
| `planning-provider-run` | Run planning provider request | WP-0600 | `runtime/planning_provider/*` | Active | Upstream only. |
| `operations-event-record` | Record operational lifecycle event | WP-0601 | `runtime/operations/status/*` | Active | Shared status source. |
| `operations-status-summary` | Summarize operational status | WP-0601 | `runtime/operations/status/*` | Active | Office-compatible. |
| `providers-list` | List operational provider catalog | WP-0604 | `config/providers/catalog.json`, `runtime/providers/catalog/status.json` | Active | Coexists with legacy `providers`. |
| `providers-show` | Show provider descriptor | WP-0604 | Same | Active | Consistent with providers-list. |
| `providers-find` | Find providers by capability | WP-0604 | Same | Active | Consistent with providers-list. |
| `providers-health-set` | Record health | WP-0607 | `runtime/providers/health/*` | Active | Manual health input. |
| `providers-capacity-set` | Record capacity | WP-0607 | `runtime/providers/health/*` | Active | Capacity in health namespace. |
| `providers-health-summary` | Summarize health/capacity | WP-0607 | `runtime/providers/health/status/*` | Active | Consumed by Operations review. |
| `worker-assignment-create` | Create assignment | WP-0608 | `runtime/workers/assignments/*` | Active | Preserves labels. |
| `worker-assignment-update` | Update assignment | WP-0608 | `runtime/workers/assignments/*` | Active | Coherent. |
| `worker-assignment-list` | Render assignment board | WP-0608 | `runtime/workers/assignments/status/board.json` | Active | Office-ready board. |
| `orchestrator-cycle` | Run bounded cycle without provider execution | WP-0609 | `runtime/orchestrator/runtime/*`, `runtime/orchestrator/dispatch/*` | Active | Correctly stops pre-provider. |
| `orchestrator-dispatch-list` | List Orchestrator dispatch records | WP-0609 | `runtime/orchestrator/dispatch/status/queue.json` | Active | Name distinguishes Orchestrator dispatch. |
| `operations-review` | Generate Traffic Controller / Operations Manager review | WP-0610 | `runtime/operations/control/*` plus inspected queues | Active | Control-plane only. |
| `operations-decide` | Record operations decision | WP-0610 | `runtime/operations/control/decisions/*` | Active | Does not execute. |
| `operations-decisions-list` | List operations decisions | WP-0610 | `runtime/operations/control/decisions/*` | Active | Coherent. |
| `codex-bridge` | Validate/run bounded Codex CLI bridge request | WP-CODEX-BRIDGE-IMPLEMENTATION | `runtime/codex_bridge/*` | Active | Adapter-like, not Orchestrator-coupled. |
| `execution-activity` | Generate execution activity snapshot | WP-EXECUTION-ACTIVITY-SURFACE-001 | `runtime/execution_activity/*`, `runtime/codex_bridge/*` | Active | Execution visibility surface. |
| `execution-activity-report` | Generate execution activity report | WP-EXECUTION-ACTIVITY-SURFACE-001 | `runtime/execution_activity/report.md` | Active | Reporting only. |
| `execution-dispatch enqueue` | Enqueue provider-agnostic execution request | WP-EXECUTION-DISPATCH-QUEUE-001 | `runtime/execution_dispatch/queue.json` | Active | Lower-level than Orchestrator dispatch. |
| `execution-dispatch list` | List execution dispatch items | WP-EXECUTION-DISPATCH-QUEUE-001 | Same | Active | Coherent. |
| `execution-dispatch inspect` | Inspect execution dispatch item | WP-EXECUTION-DISPATCH-QUEUE-001 | Same | Active | Coherent. |
| `execution-dispatch update-state` | Update execution dispatch item state | WP-EXECUTION-DISPATCH-QUEUE-001 | Same/events | Active | Manual state mutation. |
| `execution-dispatch block` | Block execution dispatch item | WP-EXECUTION-DISPATCH-QUEUE-001 | Same/events | Active | Coherent. |
| `execution-dispatch attention` | Mark attention flag | WP-EXECUTION-DISPATCH-QUEUE-001 | Same/events | Active | Coherent. |
| `execution-dispatch cancel` | Cancel execution dispatch item | WP-EXECUTION-DISPATCH-QUEUE-001 | Same/events | Active | Coherent. |
| `execution-dispatch complete` | Complete execution dispatch item | WP-EXECUTION-DISPATCH-QUEUE-001 | Same/events | Active | Coherent. |
| `execution-dispatch prepare-handoff` | Prepare Codex Bridge request | WP-EXECUTION-DISPATCH-QUEUE-001 | `runtime/execution_dispatch/handoffs/*` | Active | Adapter boundary candidate. |
| `execution-dispatch snapshot` | Generate current snapshot | WP-EXECUTION-DISPATCH-QUEUE-001 | `runtime/execution_dispatch/current.json` | Active | Visibility only. |
| `execution-dispatch-report` | Generate dispatch report | WP-EXECUTION-DISPATCH-QUEUE-001 | `runtime/execution_dispatch/report.md` | Active | Visibility only. |
| `providers` | Legacy provider registry listing | Legacy service registry | `data/registry/providers.json` | Active legacy | Name conflicts conceptually with `providers-list`. |

CLI commands inventoried: 33.

## Models / Contracts Inventory

| Model name | File path | Responsibility | Overlaps with | Recommended source of truth |
| --- | --- | --- | --- | --- |
| `PlanningProviderRequest` / response/events | `src/estate/core/planning_provider.py` | Planning-provider request/result contract | Orchestrator intake mission fields | Keep as planning input contract. |
| `OperationalEvent` | `src/estate/core/operational_events.py` | Shared lifecycle event contract | Codex Bridge lifecycle events, execution activity events | Source of truth for Estate operational status events. |
| `OrchestratorIntakeRequest` / status | `src/estate/core/orchestrator_intake.py` | Intake contract | Execution dispatch request mission/path fields | Source of truth for Orchestrator intake. |
| `OrchestratorIntakeDecision` | `src/estate/core/orchestrator_intake_decisions.py` | Intake approval/block/defer | Operations decisions | Keep separate; intake-specific. |
| `OrchestratorScheduleRecord` | `src/estate/core/orchestrator_scheduler.py` | Scheduling skeleton output | Dispatch record | Keep as schedule source. |
| `OrchestratorDispatchRecord` | `src/estate/core/orchestrator_dispatch.py` | Orchestrator dispatch record before provider execution | Execution dispatch item | Source of truth before adapter boundary. |
| `ProviderDescriptor` / `ProviderCatalog` | `src/estate/core/provider_catalog.py` | Operational provider catalog/capabilities | `data/registry/providers.json`, provider capabilities | Make operational provider source of truth. |
| `ProviderHealthRecord` | `src/estate/core/provider_health.py` | Provider health observation | Provider capacity | Keep; summarize with capacity. |
| `ProviderCapacityRecord` | `src/estate/core/provider_capacity.py` | Provider capacity observation | Provider health | Keep but consider `runtime/providers/capacity` namespace. |
| `WorkerAssignmentRecord` | `src/estate/core/worker_assignments.py` | Worker/A2C assignment board contract | Operations decisions assignment fields | Source of truth for assignments. |
| `OperationsDecision` / review | `src/estate/core/operations_manager.py` | Traffic Controller / Operations Manager decisions | Intake decisions | Keep control-plane distinct. |
| `ExecutionDispatchRequest` / item | `src/estate/core/execution_dispatch.py` | Provider-adapter dispatch queue item | Orchestrator dispatch record | Source of truth after adapter boundary. |
| `CodexBridgeRequest` / result | `src/estate/core/codex_bridge.py` | Codex CLI adapter request/result | Execution dispatch handoff | Provider-specific adapter contract candidate. |
| Execution activity event/snapshot | `src/estate/core/execution_activity.py` | Normalized execution visibility | Operational status events, Codex events | Source of truth for execution activity visibility. |
| Office operational activity view model | `src/estate/core/office_operational_activity.py` | Office panel data from operations status | Execution activity | Keep Office status-specific. |
| Office traffic controller view model | `src/estate/core/office_traffic_controller_panel.py` | Office panel data from operations control | Operations review | Keep panel-specific. |

Models inventoried: 16.

## Office Surfaces Inventory

| Surface/panel | Data source | Action controls | Status | Conflict notes |
| --- | --- | --- | --- | --- |
| Office Operational Activity Panel | `runtime/operations/status/latest.json`, `active.json`, `recent.json`, `summary.md` | Read-only activity/status | Active | Does not read execution activity. |
| Office Traffic Controller Panel | `runtime/operations/control/status/latest.json`, `summary.json`, `summary.md`, reviews, decisions | Read-only panel over Operations review/decisions | Active | Correctly distinct from Orchestrator. |
| Worker Assignment Board | `runtime/workers/assignments/status/board.json`, `summary.md` | CLI create/update/list; Office can consume board | Active | Preserves labels, no hardcoded seat count found. |
| Provider catalog/status surface | `runtime/providers/catalog/status.json` | Provider list/show/find CLIs | Active | Duplicate legacy provider registry risk. |
| Provider health/capacity summary | `runtime/providers/health/status/summary.json`, `summary.md` | Health/capacity set CLIs | Active | Used by Operations review, not scheduling policy. |
| Execution Activity Surface | `runtime/execution_activity/current.json`, `report.md`; `runtime/codex_bridge/*` | CLI report generation | Active | Not yet unified with Office activity panel. |
| Execution Dispatch Queue Surface | `runtime/execution_dispatch/current.json`, `report.md`, queue | CLI queue controls | Active | Lower-level than Orchestrator dispatch. |

Office surfaces inventoried: 7.

## Validation Artifacts Inventory

| Artifact | Package/source | Command run | Status | Notes |
| --- | --- | --- | --- | --- |
| `operations/validation/reports/WP-0612_operations_execution_integration_audit.md` | WP-0612 | Created by audit | Created | Human audit report. |
| `runtime/validation/work_packages/WP-0612_validation.json` | WP-0612 | Created by audit | Created | Machine validation receipt. |
| `docs/architecture/operations_execution_integration_findings.md` | WP-0612 | Created by audit | Created | Architecture findings summary. |
| `collaboration/work_packages/completions/WP-CODEX-BRIDGE-IMPLEMENTATION_codex_done.json` | Codex Bridge | Read/inventoried | Present | Completion receipt present. |
| `collaboration/work_packages/completions/WP-EXECUTION-ACTIVITY-SURFACE-001_codex_done.json` | Execution Activity | Read/inventoried | Present | Completion receipt present. |
| `collaboration/work_packages/completions/WP-EXECUTION-DISPATCH-QUEUE-001_codex_done.json` | Execution Dispatch | Read/inventoried | Present | Completion receipt present. |
| `runtime/validation/work_packages/*.json` | Historical validation | Existing convention | Present | Many historical receipts exist. |
| `operations/validation/reports/*.md` | Historical validation | Existing convention | Present | Many historical reports exist. |
| Audit command output | Local audit | `PYTHONPATH=src python -m estate.cli.main audit` | Failed | Linux run exposed Windows `.estate.bat` assumptions and missing discovery artifacts. |
| Focused pytest output | Local tests | `PYTHONPATH=src pytest -q ...` | Passed | 159 passed. |

Validation artifacts inventoried: 10.

## Duplicate and Conflict Analysis

Duplicates found: 6.

1. **Provider registry/catalog duplication**: legacy `data/registry/providers.json` and operational `config/providers/catalog.json` both describe providers. Operational stack should use `config/providers/catalog.json` as the source of truth for provider execution/capability discovery.
2. **Dispatch queue duplication by layer**: Orchestrator dispatch queue and Execution Dispatch Queue are both named dispatch queues. They are compatible if an adapter-boundary contract maps between them.
3. **Event stream duplication by layer**: operations status events, Codex Bridge lifecycle events, and execution activity events coexist. Boundaries should be documented so Office consumers do not treat provider lifecycle events as global operations status.
4. **Activity visibility split**: Office Operational Activity reads operations status while Execution Activity reads execution/Codex sources. This is acceptable short term but risks divergent Office visibility.
5. **Health/capacity namespace overlap**: health and capacity both write under `runtime/providers/health/records`; this is not immediately broken but should be made explicit or split.
6. **CLI provider naming overlap**: legacy `providers` and operational `providers-list/show/find` commands coexist.

Conflicts found: 4.

1. The broad `audit` command assumes Windows `.estate.bat` invocation and fails under Linux shell.
2. The future adapter boundary is not expressed as a contract, so Orchestrator dispatch and Execution Dispatch Queue may drift.
3. Scheduling observes catalog availability but does not yet consume provider capacity summary as an authoritative scheduling input.
4. Execution Activity is not integrated into the Office Operational Activity panel, creating possible visibility gaps after provider execution is added.

## Compatibility Chain Analysis

| Link | Status | Notes |
| --- | --- | --- |
| Planning Provider -> Orchestrator Intake | Compatible with manual/CLI handoff | No automatic bridge required by current packages. |
| Orchestrator Intake -> Intake Decision | Compatible | Decision controls operate over intake artifacts. |
| Intake Decision -> Schedule | Compatible | Scheduler loads intake queue/latest records. |
| Schedule -> Orchestrator Cycle | Compatible | Cycle reads schedule queue and writes dispatch records. |
| Orchestrator Cycle -> Dispatch Record | Compatible | Runtime stops at dispatch record creation. |
| Dispatch Record -> Execution Provider Adapter Contract | **Missing** | This is the intended next boundary, but repair should formalize mapping first. |
| Execution Provider Adapter Contract -> Execution Dispatch Queue | Plausible | Execution Dispatch Queue has fields required for provider handoff. |
| Execution Dispatch Queue -> Codex Bridge | Compatible | `prepare-handoff` writes Codex Bridge request. |
| Codex Bridge -> Execution Activity | Compatible | Execution Activity ingests Codex Bridge event/status sources. |
| Execution Activity -> Office Visibility | Partial | CLI/report exists; Office panel integration not audited as present. |
| Operations Manager -> Orchestrator | Compatible separation | Operations review inspects queues and records decisions, does not execute. |

## Recommended Consolidation / Repair Packages

1. **WP-0613 Consolidation Repair: Provider and Dispatch Boundary Contract**
   - Declare `config/providers/catalog.json` as operational provider source of truth.
   - Document `data/registry/providers.json` as legacy service registry or add a sync rule.
   - Add a schema/mapping document from `OrchestratorDispatchRecord` to `ExecutionDispatchRequest` without implementing routing.
2. **WP-0614 Event and Activity Surface Boundary Repair**
   - Document operations status events vs execution lifecycle events vs execution activity snapshots.
   - Decide whether Office Operational Activity should include execution activity read-only summaries.
3. **WP-0615 Provider Health/Capacity Scheduling Contract**
   - Document how scheduling should eventually consume health/capacity without adding policy yet.
4. **WP-0616 Linux Audit Command Repair**
   - Fix broad audit command assumptions around `.estate.bat` when running in non-Windows shells.

## Local Commands and Test Results

- `git status --short`: passed; initial tree was clean.
- `./estate.bat audit`: failed with permission denied in Linux.
- `PYTHONPATH=src python -m estate.cli.main audit`: failed; broad audit ran but reported 43 failures caused primarily by Windows `.estate.bat` assumptions and missing discovery runtime artifacts.
- `PYTHONPATH=src pytest -q tests/test_planning_provider.py tests/test_planning_provider_registry.py tests/test_planning_provider_runtime.py tests/test_office_operational_activity.py tests/test_orchestrator_intake.py tests/test_orchestrator_intake_decisions.py tests/test_orchestrator_intake_runtime.py tests/test_orchestrator_scheduler.py tests/test_orchestrator_schedule_runtime.py tests/test_provider_catalog.py tests/test_provider_capabilities.py tests/test_provider_health.py tests/test_provider_capacity.py tests/test_worker_assignments.py tests/test_worker_assignment_runtime.py tests/test_orchestrator_runtime.py tests/test_orchestrator_dispatch.py tests/test_orchestrator_cycle.py tests/test_operations_manager.py tests/test_traffic_controller.py tests/test_office_traffic_controller_panel.py tests/test_execution_activity.py tests/test_execution_dispatch.py`: passed, 159 tests.
- `PYTHONPATH=src pytest -q tests/test_codex_bridge.py`: passed, 18 tests.

## Acceptance Criteria Confirmation

- Local audit was run: yes, with Linux/Windows-wrapper failures recorded.
- Focused tests were attempted where present: yes.
- Runtime paths inventoried: yes.
- CLI commands inventoried: yes.
- Model/contract overlap inventoried: yes.
- Office surfaces inventoried: yes.
- Validation artifacts inventoried: yes.
- Duplicate/conflict findings documented: yes.
- Codex Bridge boundary assessed: yes.
- Recommendation for next package is clear: Consolidation Repair.
- Validation JSON exists: yes.
- No new orchestration behavior implemented: yes.
- No provider execution behavior added: yes.
- No new office created: yes.
