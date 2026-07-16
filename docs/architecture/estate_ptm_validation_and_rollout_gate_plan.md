# Estate PTM Validation and Rollout Gate Plan

Status: Draft implementation-preparation artifact for PTM-07 Gate E
Campaign: PTM-07 — Validation and rollout planning
Packages: TEST-PTM-001A, TEST-PTM-001B, ROLL-PTM-001A, ROLL-PTM-001B
Date: 2026-07-16

## Authority and boundaries

This artifact satisfies the PTM-07 bounded deliverables for validation commands, end-to-end acceptance evidence, operational rollout, resident training, pilot acceptance, expansion gating, and adoption receipts. It is source-backed by the accepted PTM baseline, the PTM parallel execution plan, the PTM dependency and parallelism plan, the package/campaign/dependency manifests, the promoted Pending package files, the source planning drafts, the PTM backlog, WP-0659, and WP-0660.

This artifact does not authorize production PTM code, does not execute rollout, does not merge implementation branches, and does not create a second dispatch queue, second registry, second scheduler, local-worker route, or new governance authority. Future execution must use the frozen PTM event envelope, command envelope, ID formats, projection envelope, intake/dedupe surface, route/deep-link surface, schedule readiness gate, dispatch evidence chain, migration slice, and validation contracts established by upstream PTM packages.

## Gate E dependency evidence

PTM-07 may proceed only when the upstream completion receipts named by the dependency manifest are present and current enough for Chief Architect review. For this Gate E planning pass, the repository contains completion receipts for every hard dependency required by the four PTM-07 packages:

| PTM-07 package | Hard dependencies | Required evidence path pattern |
| --- | --- | --- |
| TEST-PTM-001A | CORE-PTM-003B, INTAKE-PTM-001B, SCHED-PTM-001A | `collaboration/work_packages/completions/<dependency>_completion_receipt.md` |
| TEST-PTM-001B | KPI-PTM-001, DISPATCH-PTM-001, MIG-PTM-001B, UI-PTM-002, CONV-PTM-001 | `collaboration/work_packages/completions/<dependency>_completion_receipt.md` |
| ROLL-PTM-001A | TEST-PTM-001B | `collaboration/work_packages/completions/TEST-PTM-001B_completion_receipt.md` after this package completes |
| ROLL-PTM-001B | ROLL-PTM-001A | `collaboration/work_packages/completions/ROLL-PTM-001A_completion_receipt.md` after this package completes |

If any required upstream receipt is missing, stale, or contradicts a frozen contract, PTM-07 must stop and replan before formal acceptance or rollout work continues.

## TEST-PTM-001A automated replay gate and policy validation plan

TEST-PTM-001A defines the automated replay and policy gate that future PTM validation packages must run before acceptance. The gate validates append-only replay, schemas, links, permissions, and the absence of alternate execution paths without changing production PTM code.

### Replay gate command set

The future executable validation suite should expose these deterministic checks as a single gate, while allowing each check to be run independently for diagnosis:

```bash
ptm validate replay --ledger <event-log> --projections task,portfolio,schedule,financial,kpi --strict
ptm validate schema --events --commands --ids --projections --strict
ptm validate links --workspace-routes --resident-commands --dispatch-evidence --migration-sources
ptm validate policy --permissions --authority-boundaries --no-local-worker-route
ptm validate topology --no-second-queue --no-second-registry --no-second-scheduler
```

The command names are implementation-ready placeholders for the future test suite. They do not establish a second registry or scheduler; each command must read canonical PTM contracts and source-backed artifacts already accepted upstream.

### Required replay assertions

- Replaying the canonical event ledger from an empty projection store must yield deterministic task, portfolio, schedule, financial, utilization, and KPI projection snapshots.
- Each replayed event must validate against the frozen event envelope, command envelope, identifier format, and projection envelope.
- Projection replay must reject missing source hashes, duplicate event identifiers, out-of-order hash-chain links, and command envelopes without accepted authority references.
- Read-only source adapters, governed intake candidates, file-import reports, dispatch evidence chains, and migration dry-run reports must link to canonical records by path, event ID, report ID, or accepted external reference.
- Permission validation must prove that Helen, Grace, Traffic Controller, Chief Architect, Steward, Codex, and Resident-visible surfaces remain within accepted authority boundaries.
- Topology validation must fail if it detects a second dispatch queue, second registry, second scheduler, local-worker routing for this cycle, or any new governance authority.

### Evidence outputs

A passing TEST-PTM-001A gate must produce a replay report containing:

```yaml
ptm_validation_replay_report:
  report_id: string
  generated_at: iso8601
  source_refs:
    ledger_ref: string
    manifest_refs: [string]
    contract_refs: [string]
  replay_result: pass | fail | blocked
  schema_result: pass | fail | blocked
  link_result: pass | fail | blocked
  policy_result: pass | fail | blocked
  topology_result: pass | fail | blocked
  projection_hashes:
    task: string
    portfolio: string
    schedule: string
    financial: string
    kpi: string
  warnings: [string]
  blocking_findings: [string]
```

## TEST-PTM-001B end-to-end acceptance validation package draft

TEST-PTM-001B defines the formal end-to-end acceptance package for a complete PTM build. It must run after KPI, dispatch, migration, UI, and conversation dependencies are accepted.

### Acceptance package stages

1. **Dependency receipt review:** confirm required upstream receipts and Gate D migration/dispatch evidence are present.
2. **Canonical replay:** run the TEST-PTM-001A replay, schema, link, policy, and topology gate.
3. **Intake-to-task scenario:** validate governed intake, duplicate handling, task creation, projection update, and audit evidence for a representative work-package source.
4. **File-import scenario:** validate a dry-run import report, source hashes, duplicate decisions, rollback actions, and migration candidate evidence.
5. **Schedule-to-dispatch scenario:** validate schedule readiness labels, dispatch evidence-chain links, blocked-state handling, and non-creation of a second queue.
6. **Visibility and Resident scenario:** validate workspace routes, Office cards, Resident command responses, conversation links, and permission-bound response content.
7. **KPI and acceptance scenario:** validate KPI rollups, quality dashboard signals, adoption metrics, warnings, and acceptance evidence.
8. **Rollback and exception scenario:** validate rejected, duplicate, superseded, blocked, and migration-aborted paths with source-backed findings.

### End-to-end acceptance report

A future E2E run must produce one acceptance report that is suitable for Chief Architect review:

```yaml
ptm_e2e_acceptance_report:
  report_id: string
  generated_at: iso8601
  campaign_gate: Gate E
  scenario_results:
    dependency_receipts: pass | fail | blocked
    automated_replay_gate: pass | fail | blocked
    intake_to_task: pass | fail | blocked
    file_import: pass | fail | blocked
    schedule_to_dispatch: pass | fail | blocked
    visibility_and_resident: pass | fail | blocked
    kpi_and_acceptance: pass | fail | blocked
    rollback_and_exceptions: pass | fail | blocked
  accepted_contract_versions:
    event_contract_ref: string
    projection_contract_ref: string
    intake_contract_ref: string
    route_contract_ref: string
    schedule_contract_ref: string
    dispatch_contract_ref: string
    migration_contract_ref: string
  evidence_refs: [string]
  unresolved_risks: [string]
  go_no_go_recommendation: go | no_go | go_with_conditions
```

No scenario may self-accept. Any `fail` or unresolved `blocked` result forces a no-go recommendation unless the Chief Architect explicitly records a bounded waiver.

## ROLL-PTM-001A operational runbook and resident training plan

ROLL-PTM-001A defines the operational runbook, training sequence, monitoring cadence, and exception channels needed after TEST-PTM-001B is accepted.

### Operational runbook

| Phase | Operator action | Required evidence | Stop condition |
| --- | --- | --- | --- |
| Pre-rollout | Review TEST-PTM-001B acceptance report, unresolved risks, and go/no-go recommendation. | Accepted Gate E report path and Chief Architect review note. | Any unwaived `fail` or `blocked` validation result. |
| Pilot enablement | Enable PTM pilot for the accepted source slice and authorized Resident-visible surfaces only. | Pilot scope note, enabled route list, and permission matrix. | Request to broaden scope beyond accepted pilot. |
| Daily monitoring | Review replay status, import warnings, schedule readiness, dispatch evidence, KPI drift, Resident feedback, and exception queue. | Daily monitoring note with links to reports. | New second queue/registry/scheduler indicator or authority-boundary breach. |
| Exception triage | Route validation failures, permission concerns, Resident confusion, migration rollback, and dispatch-blocked states to the named authority owner. | Exception record with owner, status, and source evidence. | Governance change requested outside accepted authority. |
| Review closeout | Summarize pilot health, training completion, unresolved risks, and proposed expansion decision. | Pilot closeout report and adoption receipt. | Missing acceptance evidence or unreviewed operational incidents. |

### Resident training plan

Training must be concise, role-appropriate, and evidence-backed:

- **Orientation:** explain what PTM can show, what it cannot decide, and where Resident-visible responses come from.
- **Finding work:** demonstrate workspace deep links, Office cards, schedule views, task/project summaries, and KPI status.
- **Command safety:** explain accepted Resident command patterns, permission boundaries, blocked responses, and escalation routes.
- **Evidence literacy:** show how source paths, validation reports, dispatch evidence, and acceptance receipts are referenced.
- **Exception handling:** train Residents to report missing links, stale task states, incorrect schedule readiness, or confusing command responses.

Training completion evidence must list trainee role, covered modules, date, trainer/reviewer, outstanding questions, and links to supporting runbook sections.

### Monitoring cadence and exception channels

- Daily pilot monitoring during the initial rollout window.
- Twice-weekly review after the pilot has seven consecutive days without unwaived severity-one findings.
- Weekly Chief Architect summary until expansion is approved or the pilot is closed.
- Exception channels: validation findings to Chief Architect, operational incidents to Grace/Ops, dispatch readiness concerns to Traffic Controller, authority or budget concerns to Steward, and Resident command confusion to the Resident-support owner named in the rollout record.

## ROLL-PTM-001B rollout acceptance and expansion gate package

ROLL-PTM-001B defines the pilot acceptance, expansion gates, KPI monitoring, and adoption receipt package. It may run only after ROLL-PTM-001A training/runbook evidence exists.

### Pilot acceptance criteria

The pilot is acceptable only when all criteria below are true or explicitly waived by the Chief Architect with Steward review where authority or rollout gates are implicated:

- TEST-PTM-001B report recommends `go` or `go_with_conditions` with every condition assigned and tracked.
- Operational runbook has been used for at least one pilot monitoring cycle.
- Resident training completion evidence exists for the pilot participants.
- Replay, policy, topology, route, dispatch evidence, migration rollback, and KPI checks are passing or have bounded waivers.
- No second queue, second registry, second scheduler, local-worker route, or new governance authority has been introduced.
- Pilot adoption metrics and exception history are sufficient to evaluate expansion risk.

### Expansion gates

| Gate | Expansion decision | Required evidence |
| --- | --- | --- |
| Gate E.1 | Continue pilot without expansion | Daily monitoring evidence and unresolved-risk register. |
| Gate E.2 | Expand to the next accepted source slice or Resident cohort | Passing validation report, training receipt, KPI/adoption trend, and Chief Architect approval. |
| Gate E.3 | Pause rollout | Blocking validation, operational, authority, permission, or Resident experience finding. |
| Gate E.4 | Close pilot as accepted | Final adoption receipt, acceptance report, and expansion/steady-state recommendation. |

### Adoption receipt

A future rollout acceptance package must record adoption evidence in this shape:

```yaml
ptm_rollout_adoption_receipt:
  receipt_id: string
  generated_at: iso8601
  pilot_scope_ref: string
  validation_report_ref: string
  runbook_ref: string
  training_refs: [string]
  monitoring_refs: [string]
  kpi_summary:
    tasks_visible: integer
    resident_commands_reviewed: integer
    validation_pass_rate: number
    unresolved_severity_one_findings: integer
    unresolved_severity_two_findings: integer
  expansion_decision: continue_pilot | expand | pause | close_accepted
  decision_owner: Chief Architect | Steward
  conditions: [string]
  evidence_refs: [string]
```

## Gate E reconciliation notes

- TEST-PTM-001A provides the repeatable replay, schema, link, policy, and topology gate.
- TEST-PTM-001B packages that gate into an end-to-end validation suite and go/no-go report.
- ROLL-PTM-001A turns accepted validation into an operational runbook, resident training plan, monitoring cadence, and exception channels.
- ROLL-PTM-001B defines pilot acceptance, expansion gates, KPI/adoption monitoring, and the adoption receipt shape.
- No frozen upstream event, ID, projection, intake, route, schedule, dispatch, migration, or validation contract is redefined.
