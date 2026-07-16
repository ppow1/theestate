# Estate PTM Schedule Validation Fixtures and Critical Path Plan

Status: Implementation-ready validation artifact for future PTM schedule tests  
Campaign: `PTM-05` — Scheduling, Utilization, Financials, and KPIs  
Package: `SCHED-PTM-001B`  
Launch group: `G05B`  
Integration checkpoint: Gate C/D — schedule/finance/KPI reconciliation  
Date: 2026-07-16  
Authority baseline: Steward / Chief Architect acceptance of WP-0658, WP-0660, and WP-0661

## Purpose

This artifact defines deterministic validation fixtures for the future schedule dependency and readiness-gate implementation.

It satisfies the bounded deliverables of `SCHED-PTM-001B`, depends on the `SCHED-PTM-001A` schedule dependency and readiness-gate contract, and preserves the frozen `CORE-PTM-003B` `schedule.current_state` projection fields.

The fixtures are designed to prove that a future PTM schedule implementation can:

1. enforce dependency gates before a task can be marked dispatch-ready;
2. calculate a critical path from duration and dependency data;
3. preserve blocked intervals as schedule evidence without treating them as new governance decisions;
4. expose unknown, conflicting, incomplete, or stale source data as labeled validation failures rather than inferred readiness;
5. preserve waivers and authority references without deleting dependency evidence;
6. reuse the accepted PTM package, campaign, and dependency manifests as source authority;
7. remain deterministic across projection rebuilds and repeated fixture runs.

This is a documentation-only validation contract. It does not add production PTM code, execute or create a scheduler, dispatch work, create a second queue, create a second registry, approve schedules, approve budgets, certify readiness, or introduce a new governance authority.

## Source authority used

The artifact is source-backed by:

- `docs/architecture/estate_ptm_specification_acceptance.md`
- `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md`
- `docs/architecture/estate_ptm_dependency_and_parallelism_plan.md`
- `collaboration/work_packages/planning/estate_ptm_package_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json`
- `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json`
- `collaboration/work_packages/planning/ptm_drafts/SCHED-PTM-001B_schedule_validation_fixture_and_critical_path_plan.md`
- `collaboration/work_packages/planning/estate_project_task_management_work_package_backlog.md`
- `collaboration/reports/project_management/WP-0659_execution_lane_parallelism_and_timeline_scenarios.md`
- `collaboration/work_packages/pending/WP-0660_Correct_PTM_Execution_Decomposition_and_Hour_Scale_Timeline_Model.md`
- `docs/architecture/estate_ptm_schedule_dependency_readiness_gate_contract.md`
- `docs/architecture/estate_ptm_scheduling_projection_protocol.md`

The accepted manifests record `SCHED-PTM-001B` as:

- execution lane: Codex;
- dependency: `SCHED-PTM-001A`;
- campaign: `PTM-05`;
- launch group: `G05B`;
- integration checkpoint: Gate C/D reconciliation.

Future fixtures must remain deterministic replay inputs and must label mock records as fixture data. Production source records, completion receipts, package manifests, accepted authority records, and canonical PTM events remain authoritative in place.

## Fixture schema

Future executable tests should represent each fixture using the following stable validation envelope.

```yaml
schedule_validation_fixture:
  fixture_id: string
  description: string
  authority_context:
    package_id: SCHED-PTM-001B
    source_contract_refs: [string]
    fixture_only: true
  input_events: [object]
  input_schedule_records: [object]
  expected_schedule_records: [object]
  expected_readiness_states: [object]
  expected_critical_path:
    state: known | unknown | blocked
    task_ids: [string]
    warnings: [string]
  expected_warnings: [string]
  prohibited_side_effects:
    creates_dispatch_queue: false
    creates_registry: false
    creates_scheduler: false
    changes_governance_authority: false