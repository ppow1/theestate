# Estate Operational Current-State Map

Status: WP-0688 repository assessment
Observed at: 2026-07-17
Campaign: CAMPAIGN-0681 — Estate Operationalization
Scope: repository-integrated state only; this map introduces no runtime behavior or authority.

## Interpretation

`canonical` identifies an accepted or declared source of truth, `active` an implemented
surface, `projection` a rebuildable or derived view, `partial` an existing seam that is
not yet joined into the CAMPAIGN-0681 flow, and `provisional` an integrated artifact
whose protected acceptance remains unresolved. A file's location or an executable
mechanism never proves authority, readiness, completion, or acceptance by itself.

## Canonical systems and operational seams

| Domain | Authoritative path or seam | State, writers, and consumers | Evidence and extension seam | Freshness / duplication boundary |
|---|---|---|---|---|
| Institutional authority and offices | `docs/governance/Estate_Manual.md`, office charters and `data/registry/personnel.json` | Steward and named offices author decisions in their existing lanes; all operational consumers are read-only unless separately authorized | decision, appointment, charter, and acceptance records; reference exact authority evidence | Titles, UI placement, routing, and technical capability do not grant authority |
| Campaign definitions | `collaboration/campaigns/*.md` and exact campaign manifests | Chief Architect-authored definitions; campaign executors and review gates consume them | exact path, commit, manifest dependencies, gate record | no second campaign registry; Markdown status can drift from Git/evidence |
| Work packages | `collaboration/work_packages/` plus package templates and receipts | package owners author definitions and receipts; validators and campaigns consume them | literal WP ID, exact manifest path, commit, receipt, validation evidence | directory placement alone is not status; `completed/` and `completions/` coexist |
| CAMPAIGN-0681 execution | `src/estate/core/codex_campaign_execution.py` and accepted WP-0678 evidence | bounded campaign executor writes package commits/checkpoints; protected gate owners release gates | manifest, transition evidence, bounded commits, durable checkpoint | accepted for approved campaigns; never grants merge or acceptance |
| PTM identity and projections | `docs/architecture/estate_ptm_*` and `collaboration/work_packages/campaigns/ptm/` | canonical source records remain authoritative; PTM projections are deterministic consumers | canonical IDs, source paths/digests, append-only event/projection contracts | rollout is partial; no second ledger, ID authority, dependency graph, or scheduler |
| Operational events and status | `src/estate/core/operational_events.py`, `operational_status.py` | event writers append validated observations; status files are derived for offices | `OperationalEvent`, canonical subject references, event log and summaries | runtime status is operational, not institutional; stale/out-of-order evidence must remain visible |
| Operational campaigns | `src/estate/core/operational_campaigns.py`, `operational_campaign_runtime.py` | delegated directors invoke bounded transitions; runtime persists campaign state/events | approved authority, phase criteria, evidence, Dispatch and validation metadata | active but partial; not a replacement for CAMPAIGN-0681 manifest or gate authority |
| Grace coordination | `src/estate/core/grace_operations_runtime.py`, `runtime/operations/grace/` | Grace writes objectives, actions, checkpoints and closure observations | campaign/WP references, Dispatch requests, blocker and escalation evidence | coordination is not architecture, staffing, merge, deployment, or acceptance |
| Helen staffing | `src/estate/core/helen_workforce.py`, `runtime/hr/workforce/` | Helen writes staffing requests and assessments in the HR lane | stable campaign/WP references and capability requirements | no second personnel, worker, or capability registry; staffing is protected where policy requires |
| Alfred and mail | `src/estate/core/mailbox_index.py`, `office_mailbox_control.py`, `mailbox_sync_duty.py`, `collaboration/messages/`, `collaboration/mailboxes/index.json` | repository-backed messages are authoritative communications; indexes/folders are discovery aids | structured message with resolved personnel/mailbox IDs and canonical record references | mail is communication evidence, never campaign state, authorization, or acceptance |
| Dispatch and execution | `src/estate/core/execution_dispatch.py`, adapter handoff/runtime and provider adapters | Dispatch is the provider-neutral execution queue; authorized mechanisms update lifecycle state | campaign/WP/attempt metadata, bounded handoff, result reconciliation | no direct provider bypass or second execution queue; provider completion is not acceptance |
| Provider truth | `config/providers/catalog.json`, provider capability, health and capacity modules | provider systems write identity/health/capacity; routing consumes timestamped evidence | recommendation, selection, reservation and attempt references remain distinct | recommendations are advisory; `governed_provider_scheduler.py` is reservation-only pending reconciliation |
| Residents and services | resident registry/lifecycle modules, `src/estate/core/service_health_registry.py`, `service_status_board.py`, `operations/services/estate_service_catalog.md` | canonical resident/service mechanisms write lifecycle and health; operational views consume them | identity, health observation, timestamp, status-board link | no replacement resident or health registry; unknown and stale are not healthy |
| Capabilities | `src/estate/core/estate_capability_registry.py`, `operations/capabilities/estate_capability_registry.md` | registry owners maintain capability truth; staffing/routing/readiness consume it | capability IDs and evidence references | no campaign-local capability registry |
| Validation and evidence | `src/estate/core/work_package_validation.py`, `operations/validation/recipes/`, `reports/`, reconciliation and handoff modules | validators write reproducible verdicts; Engineering and readiness consume them | exact commands, commit SHA, outputs, recipes, reports and reconciliation | receipt is not test verdict; validation success is not acceptance |
| Readiness and post-merge closure | production readiness and `operational_readiness_closure.py` plus governed reports | readiness owners write derived verdicts; post-merge controller consumes a merge identity | validation/reconciliation/activation/publication evidence | downstream of authorized merge; cannot substitute for pre-merge review or acceptance |
| Decision support and dashboards | `docs/office/decision_support_contract.md`, office decision-support and CAMPAIGN-0680 artifacts | read-only rule-based projections consume canonical facts | evidence-backed recommendation, uncertainty, freshness and controlling links | CAMPAIGN-0680 is not a launch authority; no competing dashboard truth or decision authority |
| Continuity and reflection | `docs/operations/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md`, `operations/continuity/` | workers write governed handoffs/reflections; successors consume them | canonical artifact index, checkpoint and recovery entry point | chat and terminal memory are never authoritative |

## Current governed flow

| Stage | Existing mechanism | Operational condition | CAMPAIGN-0681 connection |
|---|---|---|---|
| Directive/intake | Steward direction, PTM/orchestrator intake, board or validation finding | heterogeneous and partly manual | reference accepted intake; do not create an intake inbox |
| Campaign/package definition | campaign Markdown, exact manifest and work-package documents | operational and repository-backed | WP-0678 executor consumes the existing graph |
| Readiness/dependencies | PTM contracts, orchestrator schedule/readiness | partial rollout and multiple legacy schedule views | derive an explainable projection; do not choose a new scheduler |
| Staffing/capability | Helen workforce and capability/provider evidence | operational, linkage sometimes ad hoc | carry stable campaign/WP/action references |
| Coordination | Grace objectives/actions/checkpoints and Alfred routing | operational but fragmented across records | normalize observations and request through existing lanes |
| Execution | canonical Dispatch, provider adapter and isolated execution | operational and deliberately authority-gated | submit only an authorized execution request |
| Validation/evidence | registered recipes, tests, reconciliation and receipts | operational; precedence can conflict | preserve every verdict/source and fail closed on conflict |
| Integration/readiness | Git/PR review followed by post-merge readiness | correctly manual/protected | observe and explain; never merge or deploy automatically |
| Acceptance/continuity | explicit authority records, completion receipts, reflection/continuity | explicit human decision required | present evidence and stop at protected gates |

## Baseline conclusion

The repository has the execution, observation, communication, validation and
continuity mechanisms needed for Estate operationalization. The missing seam is a
shared, authority-aware operational language and projection across those records.
WP-0689 may add that rebuildable contract at the existing operational-event seam;
later packages may add narrow adapters. None may turn the projection into a source
of truth or duplicate a registry, queue, scheduler, validator, dashboard, mailbox,
state store, or acceptance lane.
