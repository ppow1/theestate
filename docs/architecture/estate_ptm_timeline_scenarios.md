# Estate PTM Timeline Scenarios

This report corrects PR #360 by replacing 10-36 implementation-day projections with package-derived minute/hour estimates. Review latency, queue wait, merge delay, Steward availability, failed validation, rework, and blocked dependencies are modeled separately from active execution.

Package library contains 28 bounded packages: SPEC-PTM-001, CORE-PTM-001A, CORE-PTM-001B, CORE-PTM-001C, CORE-PTM-002A, CORE-PTM-002B, CORE-PTM-003A, CORE-PTM-003B, INTAKE-PTM-001A, INTAKE-PTM-001B, FILE-PTM-001A, FILE-PTM-001B, UI-PTM-001A, UI-PTM-001B, UI-PTM-002, CONV-PTM-001, SCHED-PTM-001A, SCHED-PTM-001B, UTIL-PTM-001, FIN-PTM-001, KPI-PTM-001, DISPATCH-PTM-001, MIG-PTM-001A, MIG-PTM-001B, TEST-PTM-001A, TEST-PTM-001B, ROLL-PTM-001A, ROLL-PTM-001B. Expected active execution totals 361 minutes (6.0 hours), validation 248 minutes, and expected rework 140 minutes. All expected active estimates are 15 minutes or less; none exceeds 60 minutes.


## Scenario A — All Codex
Package sequence follows campaign order PTM-00 through PTM-07. Parallel-safe Codex groups are the manifest parallel groups. Number of Codex task submissions: 8 campaigns or 28 atomic packages. Total active Codex execution: 361 minutes (6.0 hours). Expected validation and rework: 388 minutes. One Codex lane expected wall clock: 12.5 active hours plus human gates. Concurrent Codex expected wall clock: about 4-6 active hours plus gates.

## Scenario B — Hybrid RTX 4090 plus Codex
Local-suitable audit, UI planning, utilization, migration planning, validation-plan, and operations drafts run on RTX 4090 while architecture-sensitive contracts remain with Codex. Codex active time: 209 minutes. Local active time: 147 minutes. Projected 4090 utilization: roughly 2.5 active hours over the campaign. Critical path remains specification, ledger/projection contracts, intake/schedule/financial contracts, KPI/dispatch, validation, rollout. Expected wall clock: 8-12 active hours plus review and integration checkpoints.

## Scenario C — Maximum local execution
Local decomposition overhead: 45 minutes and elevated validation/rework risk. Packages prohibited from local execution without Codex are SPEC-PTM-001, CORE-PTM-002A/B, CORE-PTM-003A/B, CONV-PTM-001, FIN-PTM-001, KPI-PTM-001, DISPATCH-PTM-001, TEST-PTM-001B, and ROLL-PTM-001B. Total local active time if all practical packages route local: 200 minutes plus overhead. Remaining Codex active time: 156 minutes. Expected wall clock: 9-14 active hours plus human gates because validation and integration risk increase.
