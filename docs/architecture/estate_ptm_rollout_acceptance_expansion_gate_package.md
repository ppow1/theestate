# Estate PTM Rollout Acceptance and Expansion Gate Package

Status: Implementation-ready validation artifact for `ROLL-PTM-001B`
Campaign: `PTM-07` / launch group `G07D`
Authority baseline: Steward / Chief Architect acceptance of WP-0658, WP-0660, and WP-0661
Execution boundary: planning and validation artifact only; no production PTM code is authorized

## 1. Purpose and authority boundary

This package defines the final PTM rollout acceptance and expansion gate. It turns the accepted `ROLL-PTM-001A` operational runbook and resident training plan into a source-backed decision package for pilot acceptance, expansion, KPI monitoring, and adoption receipts.

This artifact does not authorize production PTM code, merge rollout branches, broaden pilot scope, create a second dispatch queue, create a second registry, create a second scheduler, route this cycle to the local RTX 4090 worker, or establish a new governance authority. Any expansion decision must remain within the accepted Helen, Grace, Traffic Controller, Chief Architect, Steward, Codex, and Resident authority boundaries.

## 2. Source-backed prerequisites

| Prerequisite | Required evidence | Stop/replan condition |
|---|---|---|
| Accepted baseline | `docs/architecture/estate_ptm_specification_acceptance.md` remains the governing acceptance record for WP-0658, WP-0660, and WP-0661. | Acceptance is superseded, withdrawn, or changed to authorize new governance boundaries. |
| Campaign order | `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md` keeps rollout in the serial chain `MIG-PTM-001B → ROLL-PTM-001A → ROLL-PTM-001B` at Gate E. | `ROLL-PTM-001B` is started before `ROLL-PTM-001A` completion evidence exists. |
| Dependency model | `docs/architecture/estate_ptm_dependency_and_parallelism_plan.md` keeps PTM-07 as the validation and rollout planning campaign and identifies rollout as the last serialized wave. | Expansion is requested before formal validation and rollout evidence are accepted. |
| Manifest state | Package, campaign, and dependency manifests list `ROLL-PTM-001B` as Codex, pending path, launch group `G07D`, and dependent on `ROLL-PTM-001A`. | Manifest drift changes package scope, route, or dependency without Chief Architect review. |
| Runbook feeder | `docs/architecture/estate_ptm_operational_runbook_and_resident_training_plan.md` provides training, monitoring, and exception channels for this package. | Training evidence, monitoring cadence, or exception routing is missing or contradicts accepted authorities. |
| Validation feeder | `docs/architecture/estate_ptm_e2e_acceptance_validation_package.md` and Gate E evidence provide a go/no-go recommendation. | Any unwaived `fail` or unresolved `blocked` validation result remains open. |

## 3. Pilot acceptance gate

A PTM pilot may be accepted only when every required condition below is true or explicitly waived by the Chief Architect, with Steward review where the condition affects authority, budget, or rollout gates.

| Acceptance condition | Minimum evidence | Decision result if missing |
|---|---|---|
| Validation status | End-to-end acceptance report recommends `go` or `go_with_conditions`, and every condition has an owner and due date. | No-go or continue pilot without expansion. |
| Runbook execution | At least one monitoring cycle has used the `ROLL-PTM-001A` runbook and recorded findings. | Continue pilot only. |
| Resident training | Training receipts exist for pilot participants and cover orientation, intake/dedupe, workspace navigation, dispatch evidence, and exceptions. | Continue pilot only until training is complete. |
| KPI quality | KPI dashboard/report labels stale, unknown, estimated, optional, and unavailable inputs without flattening them into false confidence. | Pause expansion and investigate quality rules. |
| Dispatch evidence | Task-to-work-package-to-dispatch links reuse the existing dispatch path and retain Traffic Controller authority. | Pause rollout if a parallel queue is implied. |
| Topology control | Review finds no second queue, second registry, second scheduler, local-worker route, or new governance authority. | Stop and replan. |
| Exception health | Severity-one findings are zero or explicitly waived; severity-two findings have owners and aging thresholds. | Continue pilot or pause based on severity. |
| Adoption signal | Resident usage, command review, and exception history are sufficient to judge expansion risk. | Continue pilot until evidence is sufficient. |

## 4. Expansion decision gates

| Gate | Decision | Entry criteria | Required approver | Output evidence |
|---|---|---|---|---|
| E.1 | Continue pilot without expansion | Validation is acceptable but adoption, training, KPI, or exception evidence is not yet sufficient for expansion. | Chief Architect | Updated monitoring note and unresolved-risk register. |
| E.2 | Expand to next accepted source slice or Resident cohort | Acceptance conditions are met, no topology breach exists, and expansion target already fits accepted PTM contracts. | Chief Architect; Steward if authority/budget boundaries are implicated | Expansion decision note, pilot scope delta, training plan delta, and KPI watchlist. |
| E.3 | Pause rollout | Blocking validation, policy, permission, migration, dispatch, KPI, or Resident experience finding is open. | Chief Architect | Pause note, owner assignment, rollback/containment evidence, and revalidation requirement. |
| E.4 | Close pilot as accepted | Pilot objectives are met, adoption evidence is sufficient, and steady-state ownership is named. | Chief Architect; Steward for final authority acceptance if needed | Final adoption receipt and steady-state recommendation. |

Expansion may not be used to redefine frozen event, ID, projection, intake, route, schedule, dispatch, migration, validation, KPI, or authority contracts. If the next source slice requires a contract change, this package must record a stop/replan note instead of approving expansion.

## 5. KPI and adoption monitoring package

The acceptance reviewer should evaluate these measurements at each gate decision. Unknown or unavailable values must remain explicit.

| Metric | Purpose | Quality rule | Gate use |
|---|---|---|---|
| `tasks_visible` | Confirms pilot task records are visible in accepted PTM surfaces. | Count only canonical PTM records; exclude side lists. | Required for E.2 and E.4. |
| `resident_commands_reviewed` | Confirms Resident-visible command paths were exercised and reviewed. | Count reviewed commands with source evidence and permission outcome. | Required for E.2 and E.4. |
| `validation_pass_rate` | Summarizes replay, policy, topology, route, dispatch, migration, and KPI validation health. | Report denominator and blocked checks; do not treat blocked as pass. | Required for every gate. |
| `training_completion_rate` | Confirms pilot participants received role-appropriate training. | Use named training receipts; unknown participants remain unknown. | Required for E.2 and E.4. |
| `unresolved_severity_one_findings` | Guards against critical rollout harm. | Must be zero unless explicitly waived. | Blocks E.2 and E.4 by default. |
| `unresolved_severity_two_findings` | Tracks manageable but material rollout risk. | Must have owner, due date, and expansion impact. | Conditions E.1 or E.2. |
| `resident_exception_aging` | Shows whether resident-reported issues are being resolved. | Preserve oldest age and unassigned count. | Supports E.1, E.2, and E.3. |

## 6. Adoption receipt schema

A future rollout acceptance execution must record one adoption receipt for the gate decision:

```yaml
ptm_rollout_adoption_receipt:
  receipt_id: string
  generated_at: iso8601
  gate: E.1 | E.2 | E.3 | E.4
  pilot_scope_ref: string
  validation_report_ref: string
  runbook_ref: string
  training_refs: [string]
  monitoring_refs: [string]
  exception_register_ref: string
  kpi_summary:
    tasks_visible: integer | unknown
    resident_commands_reviewed: integer | unknown
    validation_pass_rate: number | unknown
    training_completion_rate: number | unknown
    unresolved_severity_one_findings: integer | unknown
    unresolved_severity_two_findings: integer | unknown
    resident_exception_aging: string
  topology_attestation:
    no_second_queue: true
    no_second_registry: true
    no_second_scheduler: true
    no_local_rtx_4090_route: true
    no_new_governance_authority: true
  expansion_decision: continue_pilot | expand | pause | close_accepted
  decision_owner: Chief Architect | Steward
  conditions: [string]
  evidence_refs: [string]
  next_review_due: iso8601 | null
```

The adoption receipt must cite source reports rather than embedding unsupported operational claims. A receipt with unknown KPI values may support `continue_pilot` or `pause`, but it may not support `expand` or `close_accepted` unless the Chief Architect records an explicit bounded waiver.

## 7. Evidence notes for future promotion

- `ROLL-PTM-001B` remains the final serial rollout gate in primary parallel group `G07D`.
- The active estimate remains within the accepted 5/10/20 minute range and below the 60 active-minute exception threshold.
- This artifact is a documentation and validation package only; no executable PTM code was touched.
- The package reuses the accepted campaign, dependency, validation, runbook, KPI, and dispatch evidence contracts rather than creating new routing or governance surfaces.
