# Estate Project and Task Management Work Package Backlog

## Recommended execution order

1. SPEC-PTM-001 acceptance and standards baseline.
2. CORE-PTM-001 read-only discovery adapters.
3. CORE-PTM-002 event ledger and ID service.
4. CORE-PTM-003 projections and audit timeline.
5. INTAKE-PTM-001 governed intake and dedupe.
6. FILE-PTM-001 file ingestion.
7. UI-PTM-001 workspace MVP.
8. UI-PTM-002 Office compact card.
9. CONV-PTM-001 resident commands.
10. SCHED-PTM-001 scheduling and dependencies.
11. UTIL-PTM-001 capacity/utilization.
12. FIN-PTM-001 financial controls.
13. KPI-PTM-001 KPI registry.
14. DISPATCH-PTM-001 dispatch/evidence linking.
15. MIG-PTM-001 migration pilot.
16. TEST-PTM-001 validation suite.
17. ROLL-PTM-001 rollout.

## Backlog entries

| ID | Category | Title | Objective | Dependencies | Expected artifacts | Lane | Acceptance summary |
|---|---|---|---|---|---|---|---|
| SPEC-PTM-001 | Specification | Accept PTM specifications | Review and approve this specification set. | None | Accepted docs and review notes | Chief Architect | Boundaries accepted; no implementation. |
| CORE-PTM-001 | Core ledger | Read-only Estate source inventory | Inspect existing Parking Lot, work-package, dispatch, validation, acceptance, Helen, Grace, Traffic, and activity artifacts. | SPEC-PTM-001 | Inventory report and adapter contracts | Codex | No mutation and all unknowns recorded. |
| CORE-PTM-002 | Core ledger | Append-only event ledger | Implement event store, schemas, hash chain, and ID minting. | CORE-PTM-001 | Schemas, CLI/library, tests | Codex | Replayable events with stable IDs. |
| CORE-PTM-003 | Audit | Current-state projections | Build task/project/schedule/financial/KPI/audit projections. | CORE-PTM-002 | Projection builders and rebuild tests | Codex | Deterministic rebuild from log. |
| INTAKE-PTM-001 | Intake | Governed intake and dedupe | Promote Parking Lot/manual/conversation candidates into canonical objects. | CORE-PTM-003 | Intake handlers and audit events | Codex | Duplicates require confirmation. |
| FILE-PTM-001 | File intake | Approved file import | Import plans/lists/maps/provider recommendations/work-package batches with SHA-256 mappings. | INTAKE-PTM-001 | Import parser and reports | Codex | Accepted/rejected/duplicate mappings preserved. |
| UI-PTM-001 | UI | Dedicated workspace MVP | Build Portfolio, Projects, Task Ledger, detail, Intake, Audit, Archive/Trash. | CORE-PTM-003 | Local workspace screens | Codex | Thousands of tasks remain navigable. |
| UI-PTM-002 | UI | Office compact summary card | Add compact card and deep links only. | UI-PTM-001 | Office card | Codex | No full system added to Office. |
| CONV-PTM-001 | Conversation integration | Resident command hooks | Governed conversational commands for create/link/priority/production/Helen/Grace/history. | INTAKE-PTM-001 | Command parser and confirmations | Codex | No private side lists. |
| SCHED-PTM-001 | Scheduling | Schedule and dependency engine | Add dates, durations, calendars, critical path, blocked intervals, and readiness gates. | CORE-PTM-003 | Schedule projections and tests | Codex | Gates enforce before Ready dispatch. |
| UTIL-PTM-001 | Utilization | Capacity/utilization model | Track worker/provider/local compute utilization and telemetry. | SCHED-PTM-001 | Utilization observations and views | Codex | Mandatory/optional/estimated data labeled. |
| FIN-PTM-001 | Financials | Budget and cost controls | Add estimates, requests, approvals, actuals, reconciliation, and routing comparison. | CORE-PTM-003 | Financial ledger and reports | Codex | Budget authority not assigned to Helen/Grace. |
| KPI-PTM-001 | KPIs | KPI registry and observations | Implement formulas, periods, quality rules, baselines, targets, and dashboards. | UTIL-PTM-001, FIN-PTM-001 | KPI catalog/runtime | Codex | Unknown/stale data protected. |
| DISPATCH-PTM-001 | Dispatch integration | Task-to-dispatch evidence chain | Link tasks to work packages, dispatch attempts, worker evidence, validation, and acceptance. | SCHED-PTM-001 | Integration views and tests | Codex | Existing Dispatch Queue reused. |
| MIG-PTM-001 | Migration | Pilot migration | Migrate one portfolio slice with source mappings and rollback plan. | DISPATCH-PTM-001 | Migration report | Codex | IDs preserved and duplicates handled. |
| TEST-PTM-001 | Testing | End-to-end validation suite | Validate files, links, Mermaid, replay, gates, permissions, and no second execution path. | All build packages | Test suite and reports | Codex | Acceptance criteria automated where practical. |
| ROLL-PTM-001 | Rollout | Operational rollout | Train residents, publish runbooks, expand portfolios, monitor KPIs. | TEST-PTM-001 | Runbooks and rollout receipt | Grace/Codex | Pilot accepted before expansion. |
