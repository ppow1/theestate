# Estate Operational Canonical-Reuse Map

Status: WP-0688 binding reuse baseline
Campaign: CAMPAIGN-0681 — Estate Operationalization

“Extend” means add a reference, validator, projection, or narrow adapter at the
named seam. It never means copy canonical state into a CAMPAIGN-0681 subsystem.
CAMPAIGN-0670 artifacts are usable only under the bounded-reuse authorization and
retain their actual status: repository-integrated or completion-submitted, not
protected-accepted.

## Package reuse matrix

| Package/capability | Reuse | Exact extension seam | Prohibited duplicate / authority risk |
|---|---|---|---|
| WP-0689 state/events | operational events/status, PTM source-reference and projection rules, canonical domain IDs | versioned schema, pure validation and rebuildable projection beside `operational_events.py` | authoritative state store, event bus, ledger, or inferred authority |
| WP-0690 action taxonomy | office charters, campaign authority, resident authority and existing mechanism policies | pure classification/evaluation contract returning evidence and required owner | authority registry, generic execution gateway, or title-based permission |
| WP-0691 health signals | resident lifecycle, service-health registry/status board, worker/provider health | read-only adapters emitting timestamped normalized observations | health registry or treating stale/unknown as healthy |
| WP-0692 momentum observation | exact campaign manifest, receipts, Git, PTM readiness and WP-0678 checkpoint evidence | derived eligibility/blocker projection with source conflicts | scheduler, package registry or dispatch queue |
| WP-0693 blockers/escalation | existing blocker fields, Grace checkpoints, Alfred/mailbox routing, authority taxonomy | classification and structured request through canonical message seam | escalation queue, mailbox bus or protected bypass |
| WP-0694 Grace | Grace runtime objectives/actions/checkpoints | CAMPAIGN-0681 read model and canonical action requests | Operations Center state store or architectural authority |
| WP-0695 Helen | Helen workforce requests/assessments and capability evidence | campaign/WP/action references on existing staffing requests | worker/personnel registry or automatic staffing |
| WP-0696 Alfred | repository messages and mailbox index/control/sync | structured route request containing canonical references | message-as-state, new mailbox, execution or acceptance authority |
| WP-0697 Engineering | CAMPAIGN-0670 integrated specifications, PTM, Dispatch and Engineering contracts | read-only operational integration at exact manifest path | Engineering scheduler/queue/validator/acceptance path; legacy WP-0697 reuse |
| WP-0698 readiness/evidence | registered recipes, reports, reconciliation, production readiness | normalized evidence facts that retain commit, command, verdict and freshness | validator or validation-equals-acceptance rule |
| WP-0699 recovery | WP-0678 campaign checkpoints, runtime recovery/replay, canonical source events | durable transition/checkpoint metadata and deterministic retry policy | hidden state store, silent retry, erased partial failure |
| WP-0700 CME | operational event/state projections plus taxonomy and canonical request seams | bounded observe/evaluate/request/verify loop | scheduler, unconstrained agent, direct Dispatch/provider bypass |
| WP-0701 policy | existing authority, classification, privacy, spending, staffing, merge/deploy and acceptance policies | fail-closed guard checks before canonical actions | new governance authority or inferred delegation |
| WP-0702 audit | existing events, receipts, validation evidence and WP-0678 transition evidence | append-only explanations and checkpoint references | mutable decision database or alternate institutional record |
| WP-0703 dashboard | office decision-support contract and CAMPAIGN-0680 read-only patterns | derived Steward view with freshness, uncertainty and source links | dashboard truth store or decision/acceptance authority |
| WP-0704 closeout | protected acceptance lane, campaign receipts and continuity mechanisms | readiness package and explicit requested decisions | automatic acceptance, closure, or third receipt directory |
| WP-0705 validation | existing pytest/recipe/reconciliation infrastructure | targeted fixtures and reports against exact commit | campaign-specific validator service |
| WP-0706 pilot | canonical mechanisms above | bounded fixtures/real records with explicit authority and recovery | production rollout, live protected action, broad disclosure |
| WP-0707 integration | one campaign branch/PR, receipts, checkpoints and acceptance lane | aggregate evidence and request for protected review | merge, deployment, acceptance or campaign closure |

## Cross-record rules

1. Preserve literal campaign/package IDs and exact manifest paths across every
   source reference; number alone does not resolve WP-0697.
2. Carry source path, content/commit identity, observation time, evidence status,
   authority basis, and conflicts. A projection must be rebuildable.
3. Keep observation, recommendation, request, authorized mechanical execution,
   office decision, protected decision and acceptance as separate records.
4. Keep routing recommendation, provider selection/reservation, Dispatch handoff,
   execution result, validation verdict, integration decision and acceptance
   separate. No successful predecessor implies its successor.
5. Preserve stale, missing, out-of-order and contradictory evidence and fail closed.
6. Never mutate historical evidence to reconcile it; supersede through a linked
   record.

## Existing overlaps that control design

- PTM/orchestrator scheduling is the dependency/readiness seam. Legacy operations
  schedulers and the governed provider scheduler may not become parallel campaign
  schedulers; provider scheduling is reservation-only until canonical precedence is
  decided.
- Operational events/status and operational campaign runtime already persist
  operational state. CAMPAIGN-0681 may normalize and project them, not create an
  Operations Center database.
- Grace, Alfred and Helen each have working records. Cross-office integration must
  call those seams without transferring authority.
- Validation, readiness and post-merge closure already exist. CAMPAIGN-0681 adds
  evidence normalization, never a second validator.
- CAMPAIGN-0680 and current office decision support establish read-only dashboard
  patterns. A Steward surface must remain derived and advisory.
- CAMPAIGN-0670 supplies integrated Engineering contracts but remains explicitly
  unaccepted; any step requiring its protected acceptance stops.
