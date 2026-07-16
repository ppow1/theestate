# Estate PTM Dependency and Parallelism Plan

Package library contains 28 bounded packages: SPEC-PTM-001, CORE-PTM-001A, CORE-PTM-001B, CORE-PTM-001C, CORE-PTM-002A, CORE-PTM-002B, CORE-PTM-003A, CORE-PTM-003B, INTAKE-PTM-001A, INTAKE-PTM-001B, FILE-PTM-001A, FILE-PTM-001B, UI-PTM-001A, UI-PTM-001B, UI-PTM-002, CONV-PTM-001, SCHED-PTM-001A, SCHED-PTM-001B, UTIL-PTM-001, FIN-PTM-001, KPI-PTM-001, DISPATCH-PTM-001, MIG-PTM-001A, MIG-PTM-001B, TEST-PTM-001A, TEST-PTM-001B, ROLL-PTM-001A, ROLL-PTM-001B. Expected active execution totals 361 minutes (6.0 hours), validation 248 minutes, and expected rework 140 minutes. All expected active estimates are 15 minutes or less; none exceeds 60 minutes.

## WP-0661 parallel fan-out correction

The campaign waves above are authorization containers, not a strict one-campaign-at-a-time execution queue. After `CORE-PTM-003B` freezes the projection contracts, `PTM-03`, `PTM-04`, `PTM-05`, and `TEST-PTM-001A` may proceed concurrently where their package-level dependencies are satisfied. `PTM-06` planning may join once `DISPATCH-PTM-001` and file-import feeders are stable; rollout packages remain serialized after formal validation. Use `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md` as the controlling midpoint integration plan for concurrent launches.

## Campaign waves
### PTM-00 — Governance acceptance
Packages: SPEC-PTM-001. Prerequisites: none. Parallel groups: G00. Maximum useful concurrency: 1. Integration checkpoint: Chief Architect review before next wave.

### PTM-01 — Read-only source inventory
Packages: CORE-PTM-001A, CORE-PTM-001B, CORE-PTM-001C. Prerequisites: PTM-00. Parallel groups: G01A, G01B. Maximum useful concurrency: 3. Integration checkpoint: Chief Architect review before next wave.

### PTM-02 — Canonical ledger and projection contracts
Packages: CORE-PTM-002A, CORE-PTM-002B, CORE-PTM-003A, CORE-PTM-003B. Prerequisites: PTM-01. Parallel groups: G02A, G02B, G02C, G02D. Maximum useful concurrency: 3. Integration checkpoint: Chief Architect review before next wave.

### PTM-03 — Governed intake and import contracts
Packages: INTAKE-PTM-001A, INTAKE-PTM-001B, FILE-PTM-001A, FILE-PTM-001B. Prerequisites: PTM-02. Parallel groups: G03A, G03B, G03C. Maximum useful concurrency: 3. Integration checkpoint: Chief Architect review before next wave.

### PTM-04 — Visibility and command surfaces
Packages: UI-PTM-001A, UI-PTM-001B, UI-PTM-002, CONV-PTM-001. Prerequisites: PTM-03. Parallel groups: G04A, G04B, G04C. Maximum useful concurrency: 3. Integration checkpoint: Chief Architect review before next wave.

### PTM-05 — Scheduling utilization financials and KPIs
Packages: SCHED-PTM-001A, SCHED-PTM-001B, UTIL-PTM-001, FIN-PTM-001, KPI-PTM-001. Prerequisites: PTM-04. Parallel groups: G05A, G05B, G05C. Maximum useful concurrency: 3. Integration checkpoint: Chief Architect review before next wave.

### PTM-06 — Dispatch evidence and pilot migration
Packages: DISPATCH-PTM-001, MIG-PTM-001A, MIG-PTM-001B. Prerequisites: PTM-05. Parallel groups: G06A, G06B. Maximum useful concurrency: 3. Integration checkpoint: Chief Architect review before next wave.

### PTM-07 — Validation and rollout planning
Packages: TEST-PTM-001A, TEST-PTM-001B, ROLL-PTM-001A, ROLL-PTM-001B. Prerequisites: PTM-06. Parallel groups: G07A, G07B, G07C, G07D. Maximum useful concurrency: 3. Integration checkpoint: Chief Architect review before next wave.

## Critical path
SPEC-PTM-001 → CORE-PTM-001A/B → CORE-PTM-001C → CORE-PTM-002A → CORE-PTM-002B → CORE-PTM-003A → CORE-PTM-003B → INTAKE/SCHED/FIN branches → KPI/DISPATCH/MIG → TEST → ROLL.
