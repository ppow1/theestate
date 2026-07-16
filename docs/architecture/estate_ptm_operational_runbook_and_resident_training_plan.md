# Estate PTM Operational Runbook and Resident Training Plan

Status: Implementation-ready rollout planning artifact for `ROLL-PTM-001A`
Campaign: `PTM-07` / launch group `G07C`
Authority baseline: Steward / Chief Architect acceptance of WP-0658, WP-0660, and WP-0661
Execution boundary: planning and validation artifact only; no production PTM code is authorized

## 1. Purpose and operating boundary

This runbook defines the operational adoption procedure, resident training plan, monitoring cadence, and exception channels for the Estate Project and Task Management (PTM) rollout. It is designed to be used only after Gate E confirms the validation and rollout go/no-go sequence. `ROLL-PTM-001A` depends on `TEST-PTM-001B`; if end-to-end acceptance validation is missing, failed, or waived without Chief Architect approval, rollout must stop and replan.

The runbook preserves the accepted PTM authority model: it does not create a second dispatch queue, second registry, second scheduler, or new governance authority. PTM operations must reuse the canonical event/projection, intake, schedule, dispatch, migration, validation, and Office/workspace contracts accepted by the upstream packages.

## 2. Source-backed rollout prerequisites

| Gate | Required evidence | Stop condition |
|---|---|---|
| Authority baseline | `docs/architecture/estate_ptm_specification_acceptance.md` remains accepted and still authorizes Codex-only preparation without altering Helen, Grace, Traffic Controller, Chief Architect, or Steward boundaries. | Any request to change authority boundaries or route this cycle to the local RTX 4090 worker. |
| Campaign order | `docs/architecture/estate_ptm_parallel_campaign_execution_plan.md` still lists rollout serialization as `MIG-PTM-001B → ROLL-PTM-001A → ROLL-PTM-001B`, with `ROLL-PTM-001A` in launch group `G07C`. | Any attempt to run resident rollout before validation evidence is complete. |
| Dependency manifest | `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json` still lists `ROLL-PTM-001A` as dependent on `TEST-PTM-001B`. | `TEST-PTM-001B` not accepted, not present, or superseded without an explicit waiver. |
| Package manifest | `collaboration/work_packages/planning/estate_ptm_package_manifest.json` still marks `ROLL-PTM-001A` as Codex execution, pending path `collaboration/work_packages/pending/ROLL-PTM-001A_Operational_runbook_and_resident_training_plan.md`, group `G07C`, and Gate E. | Manifest drift that changes lane, package scope, or checkpoint. |
| Campaign manifest | `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json` keeps PTM-07 serialized through `TEST-PTM-001A`, `TEST-PTM-001B`, `ROLL-PTM-001A`, then `ROLL-PTM-001B`. | Direct dependency chain is skipped or parallelized for execution. |

## 3. Operator runbook

### 3.1 Pre-rollout checklist

1. Confirm `TEST-PTM-001B` has a completion receipt and the Chief Architect has not recorded a blocker.
2. Confirm the active branch has been rebased and reviewed for collision against `collaboration/reports` and `docs/architecture`.
3. Confirm no local RTX 4090 worker routing is used for this cycle.
4. Confirm upstream contract-freeze surfaces are unchanged: event/ID, projection, intake/dedupe, workspace routes, schedule readiness, dispatch evidence, validation evidence, and migration source mappings.
5. Publish the current support rota: primary operator, Chief Architect escalation, Grace/Ops training owner, Traffic Controller dispatch contact, and Steward decision contact.
6. Prepare resident training material from section 4 and exception intake language from section 6.

### 3.2 Go/no-go sequence

| Step | Owner | Action | Evidence to retain |
|---|---|---|---|
| 1 | Codex package owner | Attach this runbook and evidence note to the package branch. | Completion receipt path and PR link. |
| 2 | Chief Architect | Review Gate E validation evidence from `TEST-PTM-001B`. | Go/no-go note or explicit waiver. |
| 3 | Grace/Ops | Confirm resident-facing instructions are understandable and do not imply new authorities. | Training dry-run note. |
| 4 | Traffic Controller | Confirm PTM dispatch links use the existing dispatch route and do not form a parallel queue. | Dispatch route confirmation. |
| 5 | Steward / Chief Architect | Approve operational training start or direct replan. | Approval note in PR/review thread. |

### 3.3 Day-0 operating procedure

- Start in observation mode: residents may learn the PTM surfaces and submit governed intake, but operators must not broaden scope beyond the validated package set.
- Route all new work through the accepted intake/dedupe and command paths; do not accept private side lists as canonical PTM entries.
- Keep dispatch evidence tied to canonical task/work-package/dispatch links.
- Record every exception using the exception channels in section 6.
- If a resident discovers stale, unknown, or missing data, label it as such rather than inventing status.

### 3.4 Stop/replan triggers

Stop rollout and open a replan note if any of the following occurs:

- a dependency, completion receipt, or validation report cannot be found;
- a resident workflow requires a new queue, registry, scheduler, or governance authority;
- a frozen upstream contract must change;
- evidence suggests duplicate task creation or bypassed intake confirmation;
- financial, schedule, dispatch, or Steward authority is misrepresented;
- expected active work for this slice exceeds 60 minutes without evidence and approval.

## 4. Resident training plan

### 4.1 Training goals

Residents should leave training able to:

1. explain that PTM is the canonical project/task-management surface, not a second private tracker;
2. submit or inspect tasks through governed intake and accepted resident command surfaces;
3. recognize confirmation, duplicate, rejected, stale, unknown, and evidence-required states;
4. follow task-to-dispatch evidence links without bypassing Traffic Controller controls;
5. use exception channels when PTM data appears wrong or incomplete.

### 4.2 Training sequence

| Module | Duration target | Content | Completion signal |
|---|---:|---|---|
| Orientation | 5 minutes | PTM purpose, authority boundaries, no second queue/registry/scheduler. | Resident can state what PTM is not allowed to replace. |
| Intake and dedupe | 7 minutes | Manual, Parking Lot, conversation, and file-import inputs all resolve through governed intake semantics. | Resident can identify when confirmation is required. |
| Workspace navigation | 5 minutes | Workspace and Office compact-card summaries are views of canonical PTM data. | Resident can find a task without using side lists. |
| Dispatch evidence | 5 minutes | Task/work-package/dispatch linkage and Traffic Controller channel expectations. | Resident can explain where dispatch evidence lives. |
| Exceptions | 5 minutes | How to report missing data, duplicate entries, failed validation, or authority concerns. | Resident submits or narrates a sample exception. |

### 4.3 Training materials checklist

- one-page resident quick-start: canonical PTM surfaces, allowed actions, and forbidden side-list behavior;
- exception template: summary, observed PTM ID or source reference, expected result, actual result, urgency, authority impact;
- operator crib sheet: stop/replan triggers, escalation route, and monitoring cadence;
- attendance or acknowledgement note for residents who receive training.

## 5. Monitoring cadence

| Period | Cadence | Review focus | Owner |
|---|---|---|---|
| Day 0 | Before and after first training session | Gate E evidence, support rota, first resident questions, any authority confusion. | Grace/Ops with Chief Architect backup |
| Days 1-3 | Daily | Duplicate intake, stale/unknown labels, failed command confirmations, dispatch evidence gaps, resident exceptions. | Grace/Ops |
| Weeks 1-2 | Twice weekly | KPI quality signals, schedule readiness labels, financial boundary questions, migration/source-mapping issues. | Chief Architect or delegate |
| After week 2 | Weekly until rollout acceptance | Open exception aging, training coverage, unresolved validation drift, expansion readiness. | Chief Architect / Steward review as needed |

Monitoring must use accepted PTM evidence and reports only. If an operator needs new telemetry that requires contract changes, stop and replan instead of adding ad hoc production behavior.

## 6. Exception channels

| Exception class | First channel | Escalation | Required evidence |
|---|---|---|---|
| Resident cannot complete governed intake | Grace/Ops training owner | Chief Architect if contract or UX change is needed | Resident action, PTM ID/source reference, screenshot or reproduction note if available. |
| Duplicate, stale, unknown, or missing task data | PTM exception note in the package/report evidence thread | Chief Architect for projection/ledger drift | Expected canonical state, observed state, source evidence. |
| Dispatch linkage problem | Traffic Controller contact | Chief Architect if evidence chain contract is implicated | Task ID, work-package ID, dispatch reference, missing or conflicting link. |
| Authority or budget confusion | Chief Architect | Steward if authority decision is required | Exact resident/operator wording that caused confusion. |
| Validation or migration evidence gap | Package owner / Validation lane | Chief Architect go/no-go review | Missing receipt/report path and impact statement. |

Exceptions must not be resolved by creating side queues, side registries, or undocumented resident workflows. Temporary workarounds must be recorded as exceptions and retired or formalized through a future accepted package.

## 7. Evidence required for `ROLL-PTM-001B`

This package should leave enough evidence for the future rollout acceptance and expansion gate package to decide whether to proceed. Minimum evidence:

- this runbook committed and cited in the package completion receipt;
- validation command output for `git diff --check`;
- dependency and manifest revalidation note;
- explicit no-second-queue/no-second-registry/no-new-authority statement;
- resident training modules and monitoring cadence ready for Chief Architect review;
- exception channels mapped to existing Estate roles rather than new authorities.
