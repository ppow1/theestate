# Engineering Department Current-State Map

**Assessment:** WP-0670  
**Observed at:** 2026-07-16  
**Campaign:** `CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION`  
**Scope:** repository state only; no production behavior is proposed or changed here.

## Reading this map

“Observed” means a repository artifact or executable surface exists. “Proposed” is reserved for a gap or a downstream design decision. The classifications are:

- **canonical** — the declared source of truth or governed system of record;
- **active** — implemented and connected to a current command or runtime path;
- **partial** — useful implementation exists, but the end-to-end departmental contract is incomplete;
- **stale** — retained evidence or instructions no longer describe the current mechanism;
- **superseded** — a newer named mechanism explicitly replaces it;
- **experimental** — bounded demonstration or recommendation surface, not institutional authority;
- **duplicate** — overlaps an authoritative mechanism and must not become another control plane.

These labels describe the artifact in the Engineering campaign flow; an artifact can be canonical for evidence and historical rather than executable.

## 1. Department inventory

| Artifact or surface | Classification | Observed role and authority |
|---|---|---|
| `operations/departments/engineering/engineering_department_charter.md` | canonical | Department mission, work-package discipline, local-execution principle, and authority boundaries. Steward authority in this older charter is broader than Campaign 0670’s specific Chief Architect acceptance rule; see the conflict register. |
| `operations/departments/engineering/engineering_department_operating_guide.md` | canonical | Intake, package shaping, validation, receipt, review, and blocker guidance. It is policy prose, not a durable campaign state machine. |
| `operations/departments/engineering/cuemastery_execution_handoff.md` | partial | Initial product handoff. It records that CueMastery repository discovery was still required; it is not a general campaign intake record. |
| `operations/departments/engineering/WP-0125_engineering_department_establishment_report.md` | canonical historical evidence | Establishment snapshot and original canonical-path declaration. Its readiness totals and Git hash are a point-in-time record, not current status. |
| `runtime/departments/engineering/WP-0125_engineering_department_establishment_report.json` and `WP-0125_engineering_department_status.json` | stale snapshot | Machine-readable establishment evidence. Neither is maintained as a live CAMPAIGN-0670 status surface. |
| `collaboration/campaigns/CAMPAIGN_0550_LOCAL_ENGINEERING_DEPARTMENT_FIRST_OPERATIONAL_SLICE.md` | canonical historical campaign contract | Settles Helen, Grace, Chief Architect, external-runtime and evidence boundaries for the first local loop. It explicitly authorizes one coherent campaign PR, unlike Campaign 0670. |
| `operations/local_engineering_department/CAMPAIGN_0550_completion_record.md` | canonical historical evidence | Human-readable result of the first slice; not a reusable campaign lifecycle record. |
| `src/estate/core/local_engineering_department.py` | active, partial | Estate adapter for the external Engineering Worker Runtime. It uses Helen, Grace, Dispatch, handoff, independent readiness validation, hashes, and non-automatic acceptance records. `run_closed_loop()` is fixed to CAMPAIGN_0550/WP-0552; `run_dispatch_bridge()` is the reusable seam. |
| `src/estate/cli/local_engineering_department.py` | active, partial | Direct `run-closed-loop` and `run-dispatch-bridge` command surface. It is a separate module entry point, not registered as a subcommand in the main CLI. |
| `scripts/Sync-EngineeringWorkerRuntime.ps1` and `external/engineering_worker_runtime/*` | active | Governed source and materialization path for the external worker at `A:\AI\Tools\EngineeringWorkerRuntime`; raw worktrees/runs remain external. |
| `src/estate/core/openwebui_engineering_workflow.py` | active, experimental | Chat-triggered Helen and Grace artifact creation. It deliberately performs no provider execution. Its objectives are hard-coded to WP-0649, so it is not general campaign intake. |
| `src/estate/core/helen_workforce.py` plus `runtime/hr/workforce/*` | canonical, active | Staffing requests and assessments. Helen supplies qualification and staffing evidence; she does not prioritize, schedule, dispatch, or accept Engineering work. |
| `src/estate/core/grace_operations_runtime.py` plus `runtime/operations/grace/*` | canonical, active | Objective/action/checkpoint/closure records and Dispatch requests. Grace maintains momentum and operational status, but `accepted=False` preserves institutional acceptance. |
| `src/estate/core/execution_dispatch.py` plus `runtime/execution_dispatch/*` | canonical, active | Provider-neutral execution queue, lifecycle, blockers, attention, completion, and snapshots. This is the only Engineering handoff queue to extend. |
| `src/estate/core/execution_adapter_handoff_runtime.py`, `execution_provider_adapter.py`, `execution_provider_adapter_runtime.py`, and `execution_result_reconciliation.py` | canonical, active | Dispatch-to-provider request boundary, provider-neutral execution, and result reconciliation. Live execution requires explicit authorization/confirmation. |
| `src/estate/core/codex_bridge_execution_provider_adapter.py` | active | Codex mapping behind the provider-neutral adapter boundary; it is an execution mechanism, not an office or authority. |
| `config/providers/catalog.json`, `src/estate/core/provider_catalog.py`, `provider_capabilities.py`, `provider_health.py`, and `provider_capacity.py` | canonical, active | Provider identity, capabilities, health, and capacity. These records must be reused rather than copied into Engineering campaign state. |
| `src/estate/core/provider_routing_recommendations.py` and `provider_routing_recommendations_runtime.py` | canonical, active | Recommendation-only routing; does not dispatch or reserve providers. |
| `src/estate/core/engineering_provider_health_runtime.py`, `engineering_capacity_runtime.py`, and `engineering_provider_routing_runtime.py` | active, partial | Engineering-facing aggregation and recommendations over canonical provider evidence. These are views/policy helpers, not a provider registry. |
| `src/estate/core/governed_provider_scheduler.py` and `runtime/engineering_scheduler/*` | active, duplication risk | Reservation/queue surface added for provider scheduling. It must be reconciled with PTM schedule readiness and Dispatch; Campaign 0670 may not make it a second Engineering scheduler or dispatch queue. |
| `src/estate/core/orchestrator_intake*.py`, `orchestrator_schedule_runtime.py`, `orchestrator_dispatch.py`, and `orchestrator_cycle.py` | canonical, active | Governed approved-intake, scheduling and Dispatch-record creation. The orchestrator does not execute providers. It is the existing automation seam where routine Steward prompting can be reduced. |
| `src/estate/core/operational_campaigns.py` and `operational_campaign_runtime.py` | active, partial | Operational campaign definition, checkpoint, board action, reporting, and validation integration. It does not currently parse Engineering campaign Markdown or decompose it into Engineering packages. |
| `src/estate/core/operations_scheduler*.py` and `autonomous_work_queue_scheduler.py` | active, legacy/overlap risk | Older operations scheduling/queue surfaces. They cannot be adopted as another Engineering queue without an explicit source-of-truth decision. |
| `collaboration/work_packages/campaigns/ptm/*` and `docs/architecture/estate_ptm_*` | canonical contract, partial rollout | PTM defines package identity, dependencies, readiness, schedule, campaign execution, dispatch evidence and rollout gates. Downstream work must extend these contracts rather than invent Engineering equivalents. |
| `collaboration/templates/work_package_v1.md`, `collaboration/work_packages/{pending,claimed,completed,completions}/` | canonical convention, partial consistency | Markdown definitions and durable receipts. Both `completed/` and `completions/` exist, and many completed definitions remain under `pending/`; location alone is therefore not truthful status. |
| `src/estate/core/work_package_validation.py`, `operations/validation/recipes/*`, `operations/validation/reports/*`, and `runtime/validation/work_packages/*` | canonical, active | Registered recipe execution and human/machine evidence. A receipt is not a substitute for a passing recipe. |
| `src/estate/core/production_readiness_validation.py` | canonical, active | Repository-wide receipt/recipe/readiness audit used by Engineering and operational closure. |
| `src/estate/core/post_merge_validation_pipeline.py`, `validation_reconciliation*.py`, and `validation_handoff_artifact_workflow.py` | canonical, active | Post-merge validation, verdict reconciliation, queue drain, handoff and audit evidence. These are integration mechanisms, not Engineering acceptance authority. |
| `src/estate/core/operational_readiness_closure.py` and `docs/operations/Operational_Readiness_Closure_Controller_v1.md` | canonical, active | Post-merge intake through validation/reconciliation/activation/publication closure. It begins with a merge commit, so it is downstream of PR acceptance and does not replace pre-merge Chief Architect review. |
| `src/estate/core/mailbox_index.py`, `office_mailbox_control.py`, `mailbox_sync_duty.py`, `collaboration/mailboxes/*`, and `collaboration/messages/*` | canonical, active | Alfred-compatible inter-office communication, routing and synchronization. Mail is communication evidence, not campaign or queue state. |
| `src/estate/core/alfred*.py` and `operations/alfred/*` | active | Alfred routes, summarizes and exposes duties. No Engineering execution or architecture approval authority is conferred. |
| `docs/operations/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md`, `docs/templates/ChatGPT_Worker_Reflection_Continuity_Template_v1.md`, and `operations/continuity/*` | canonical process, partial Engineering integration | Existing reflection and continuity record system. Engineering has no campaign-keyed notebook or renewal trigger yet. |
| `operations/engineering_capacity/*` and `operations/readiness/*` | active generated reports | Current human-readable provider/readiness views. They are derived evidence, not sources of authority or package status. |
| `collaboration/work_packages/pending/WP-0658*` through `WP-0662*` and PTM completion receipts | canonical recent planning evidence | Establish PTM decomposition, parallelism and campaign handoffs. Pending-file placement conflicts with completion receipts and demonstrates the status-drift gap. |
| `collaboration/work_packages/pending/WP-0663*` through `WP-0669*` | pending/experimental | EOC/CME architecture investigation. It must not be presumed implemented or used to invent authority in Campaign 0670. |

## 2. Current command surfaces

Observed commands registered by `src/estate/cli/main.py` include:

- workforce and operations: `helen-readiness`, Grace operations commands, and resident/office action surfaces;
- orchestration: `orchestrator-cycle`, `orchestrator-schedule`, and `orchestrator-dispatch-list`;
- dispatch: `execution-dispatch` enqueue/list/inspect/update/block/attention/cancel/complete/prepare-handoff/snapshot;
- provider boundary: `execution-provider-adapter`, `execution-adapter-handoff`, execution session/reconciliation, provider catalog/health/capacity, provider-routing recommendations, Engineering provider health/routing, and `engineering-scheduler`;
- validation/readiness: `validate-work-package`, `validation-production-readiness`, operational readiness/dashboard, and post-merge closure surfaces;
- communications: `mailbox-index`, office mailbox actions, resident mail, and mailbox synchronization duty.

Observed separate module command: `python -m estate.cli.local_engineering_department run-dispatch-bridge <dispatch-id>`. There is no single `engineering campaign intake/status/advance` command, and no need to create a second dispatcher to add one.

## 3. Observed end-to-end path

| Stage | Current observed mechanism | Durable evidence | Human prompt still normally required |
|---|---|---|---|
| 1. Approved idea | Steward direction, Chief Architect recommendation, Operations Board item, validation finding, or approved orchestrator intake | prose, board/intake record, or message | Someone must turn heterogeneous approval evidence into an Engineering campaign definition. |
| 2. Campaign | Markdown campaign documents establish scope/order/gates | `collaboration/campaigns/*.md` | Campaign identity and gate state are not registered in a common runtime record. Gate release is manual. |
| 3. Decomposition | Author writes numbered work packages; PTM contracts describe dependencies/readiness | package Markdown and PTM artifacts | No implemented Engineering adapter validates a campaign-to-package graph or materializes readiness from it. |
| 4. Staffing | Helen request and assessment | `runtime/hr/workforce/*` | Request creation and association with campaign/package IDs are ad hoc; CAMPAIGN_0550 and WP-0649 helpers hard-code identities. |
| 5. Operational assignment | Grace objective/action and optional Dispatch request | `runtime/operations/grace/*` | A caller must create the objective and decide when to request Dispatch. Grace cannot approve architecture. |
| 6. Scheduling/routing | PTM/orchestrator readiness, recommendation-only provider routing, and possibly provider reservations | PTM schedule/intake records, routing evidence, scheduler records | Choice among overlapping schedule surfaces is not declared for Engineering; provider selection is not bound to a shared campaign/package record. |
| 7. Dispatch | Canonical execution Dispatch item and handoff | `runtime/execution_dispatch/*`, handoff artifacts | A bounded eligible item must be enqueued/advanced; no campaign gate automatically authorizes it. |
| 8. Execution | Provider adapter or external Engineering Worker Runtime in isolated worktree | external raw run/worktree plus Estate references/hashes | Operator authorization is deliberately required for live execution; this is a safety gate, not unwanted Steward micromanagement. |
| 9. Validation | Targeted tests, registered recipe, independent readiness report, result reconciliation | validation reports, runtime JSON, captures, external hashes | Applicability and evidence bundle completeness are package-authored rather than enforced by a campaign contract. |
| 10. Integration | PR and Chief Architect review; no automatic merge | commit, PR, review evidence | Chief Architect must decide architecture/package acceptance and an authorized actor must merge. Correctly manual. |
| 11. Post-merge closure | Operational Readiness Closure Controller | case, validation, reconciliation, activation/publication evidence | Intake needs merge identity; blockers can require acknowledged human decisions. |
| 12. Campaign acceptance/archive | Completion receipts, campaign report, continuity/reflection artifacts | several unrelated directories and formats | There is no canonical campaign acceptance package or gate ledger. Definitions frequently remain `Pending` after receipts exist. |

## 4. Authority map (Campaign 0670 baseline)

- **Chief Architect:** owns Engineering architecture, integration-gate release, package acceptance, and campaign acceptance preparation/review. Engineering must not self-accept.
- **Steward:** supplies approved intent, priorities, exceptions, and retained institutional authority, but Campaign 0670 is explicitly meant to remove dependence on the Steward as routine scheduler. Safety confirmations and constitutional escalations remain legitimate Steward touchpoints.
- **Grace:** coordinates momentum, assignment state, checkpoints, retry/escalation within delegation, evidence collection, and operational closure. Grace does not approve architecture, merge, or declare institutional acceptance.
- **Helen:** owns roles, qualifications, staffing readiness, and personnel assignment evidence. Helen does not set Engineering priority or schedule work.
- **Alfred:** routes inter-office messages, summaries, reminders, and mailbox/duty awareness. Alfred does not execute Engineering work or own campaign state.
- **PTM/orchestrator:** supplies the governed dependency/readiness/scheduling and dispatch-request seams. It does not acquire acceptance authority.
- **Dispatch:** is the provider-neutral execution handoff queue and lifecycle record. It does not prioritize campaigns or accept results institutionally.
- **Validation/readiness:** produces reproducible verdict and closure evidence. Passing evidence informs, but does not itself exercise Chief Architect acceptance.
- **Codex/local AI/providers:** are bounded execution mechanisms selected through existing provider evidence and adapter contracts; none is an office, scheduler, or authority.

## 5. Baseline conclusions

1. The repository already contains every major execution primitive: intake/schedule, Helen staffing, Grace coordination, Dispatch, provider evidence/routing, external local execution, validation/reconciliation, post-merge closure, mailbox routing, and continuity processes.
2. The missing institution is primarily a **shared Engineering campaign/work-package contract and lifecycle projection**, not another engine.
3. The highest-risk overlaps are the several scheduling surfaces, two completion directories, hard-coded demonstration identities, and status inferred from file location.
4. Downstream packages must bind existing records with stable campaign/package identifiers and explicit authority, evidence, and recovery rules. They must not relocate or reimplement the underlying systems.

