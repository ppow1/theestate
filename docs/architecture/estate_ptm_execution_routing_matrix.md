# Estate PTM Execution Routing Matrix

Package library contains 28 bounded packages: SPEC-PTM-001, CORE-PTM-001A, CORE-PTM-001B, CORE-PTM-001C, CORE-PTM-002A, CORE-PTM-002B, CORE-PTM-003A, CORE-PTM-003B, INTAKE-PTM-001A, INTAKE-PTM-001B, FILE-PTM-001A, FILE-PTM-001B, UI-PTM-001A, UI-PTM-001B, UI-PTM-002, CONV-PTM-001, SCHED-PTM-001A, SCHED-PTM-001B, UTIL-PTM-001, FIN-PTM-001, KPI-PTM-001, DISPATCH-PTM-001, MIG-PTM-001A, MIG-PTM-001B, TEST-PTM-001A, TEST-PTM-001B, ROLL-PTM-001A, ROLL-PTM-001B. Expected active execution totals 361 minutes (6.0 hours), validation 248 minutes, and expected rework 140 minutes. All expected active estimates are 15 minutes or less; none exceeds 60 minutes.


| Package | Preferred lane | Alternate lanes | Prohibited lanes | RTX 4090 suitability | Codex necessity |
|---|---|---|---|---|---|
| SPEC-PTM-001 | Chief Architect | Codex analysis | Local RTX 4090 worker | No | Optional or review |
| CORE-PTM-001A | Local RTX 4090 worker | Codex | Production runtime changes | Yes | Optional or review |
| CORE-PTM-001B | Local RTX 4090 worker | Codex | Production runtime changes | Yes | Optional or review |
| CORE-PTM-001C | Codex | Local RTX 4090 worker | Unsupervised local merge | Yes | Required |
| CORE-PTM-002A | Codex | Local RTX 4090 worker | No-review local authority | Yes | Required |
| CORE-PTM-002B | Codex | Local RTX 4090 worker | Independent second registry | Yes | Required |
| CORE-PTM-003A | Codex | Local RTX 4090 worker | Local-only canonical decisions | Yes | Required |
| CORE-PTM-003B | Codex | Local RTX 4090 worker | Local-only canonical decisions | Yes | Required |
| INTAKE-PTM-001A | Codex | Local RTX 4090 worker | Ungoverned local task creation | Yes | Required |
| INTAKE-PTM-001B | Codex | Local RTX 4090 worker | Private side lists | Yes | Required |
| FILE-PTM-001A | Local RTX 4090 worker | Codex | Production importer changes | Yes | Optional or review |
| FILE-PTM-001B | Codex | Local RTX 4090 worker | Unreviewed import execution | Yes | Required |
| UI-PTM-001A | Local RTX 4090 worker | Codex | Production UI mutation before contract freeze | Yes | Optional or review |
| UI-PTM-001B | Codex | Local RTX 4090 worker | Second task workspace | Yes | Required |
| UI-PTM-002 | Local RTX 4090 worker | Codex | Full PTM duplicate in Office | Yes | Optional or review |
| CONV-PTM-001 | Codex | Local RTX 4090 worker | Private command side lists | Yes | Required |
| SCHED-PTM-001A | Codex | Local RTX 4090 worker | Local-only scheduling authority | Yes | Required |
| SCHED-PTM-001B | Local RTX 4090 worker | Codex | Runtime gate changes | Yes | Optional or review |
| UTIL-PTM-001 | Local RTX 4090 worker | Codex | Unlabeled inferred telemetry | Yes | Optional or review |
| FIN-PTM-001 | Codex | Local RTX 4090 worker | Local financial authority decisions | Yes | Required |
| KPI-PTM-001 | Codex | Local RTX 4090 worker | Flattening unknown data | Yes | Required |
| DISPATCH-PTM-001 | Codex | Local RTX 4090 worker | Second dispatch queue | Yes | Required |
| MIG-PTM-001A | Local RTX 4090 worker | Codex | Unapproved broad migration | Yes | Optional or review |
| MIG-PTM-001B | Codex | Local RTX 4090 worker | Unreviewed data migration | Yes | Required |
| TEST-PTM-001A | Local RTX 4090 worker | Codex | Production test changes before contracts | Yes | Optional or review |
| TEST-PTM-001B | Codex | Local RTX 4090 worker | Self-acceptance without independent review | Yes | Required |
| ROLL-PTM-001A | Grace/Ops | Codex drafting, Local RTX 4090 drafting | Local-only authorization | Yes | Optional or review |
| ROLL-PTM-001B | Chief Architect + Steward | Codex analysis | Local RTX 4090 worker | No | Optional or review |

## Kickoff recommendation
First campaign ready for Chief Architect acceptance: PTM-00. First entirely Codex executable: PTM-02 after PTM-01 evidence. First hybrid campaign: PTM-01. First RTX 4090 worker package: CORE-PTM-001A. Packages that must remain with Codex as preferred lane include architecture-sensitive ledger/projection, conversation, financial, KPI, dispatch, migration-execution, and E2E validation packages. Recommended hybrid strategy expected active execution is 361 minutes, with 246 validation minutes and 140 rework minutes; with review waits separated, expected elapsed time is about 8-12 active hours plus human gates.
