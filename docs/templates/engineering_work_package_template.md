# `<WP-ID>` — `<Title>`

Status: Pending
Primary campaign: `<CAMPAIGN_ID>`
Parent authority: `<campaign/path/digest>`
Owner: Chief Architect
Execution lane: `<lane>`
Risk class: `<standard | elevated | protected>`

## Objective

`<one bounded, acceptance-testable outcome>`

## Scope

- `<included change>`

## Non-goals / do not touch

- `<excluded path or behavior>`

## Required reading

- `<canonical artifact path and version/digest if applicable>`

## Dependencies

| ID | Type | Required state | Verification | Evidence/authority |
|---|---|---|---|---|
| `<ID>` | `<blocks | finish_to_start | start_to_start | evidence_required | approval_required>` | `<state>` | `<machine: exact query/command | manual: named verifier>` | `<reference>` |

## Ownership and collision control

- Branch: `<one implementation branch>`
- Base commit: `<sha>`
- Branch owner: `<actor>`
- Owned paths/globs: `<bounded list>`
- Known overlaps and resolution: `<sequence/dependency/integration owner>`
- Ownership release event: `<PR closed | merged | cancelled | explicit reassignment>`

## Readiness evidence

| Gate | Evidence reference | Authority | State/expiry |
|---|---|---|---|
| Architecture | `<accepted decision>` | Chief Architect | `<state>` |
| Staffing | `<assignment/capability>` | `<authority>` | `<state>` |
| Dependencies | `<records>` | `<authority>` | `<state>` |
| Provider capability | `<catalog/health>` | `<authority>` | `<state>` |
| Test environment | `<preflight>` | `<authority>` | `<state>` |
| Data/privacy | `<classification/decision>` | `<authority>` | `<state>` |
| Budget | `<approval>` | `<authority>` | `<state>` |
| Protected approvals | `<records or N/A rationale>` | `<authority>` | `<state>` |

## Deliverables

- `<path/artifact>`

## Validation recipe

Environment/preconditions: `<details>`

| Exact command/check | Required? | Expected evidence/location | Failure meaning |
|---|---|---|---|
| `<command>` | `<yes/no>` | `<artifact/result>` | `<meaning>` |

## Rollback and interruption

- Reversible units: `<commits/artifacts>`
- Restore procedure and verification: `<exact steps>`
- Rollback authority: `<actor>`
- In-flight interruption handling: `<branch/evidence/reservation disposition>`

## Completion and acceptance

Receipt: `collaboration/work_packages/completions/<WP-ID>_completion_receipt.md`

Receipt must separate execution, validation, integration and acceptance states; bind evidence to branch/commit/PR; list deliverables, commands/results, limitations, rollback and timestamps. Passing validation or writing the receipt is not acceptance. Acceptance actor: Chief Architect.
