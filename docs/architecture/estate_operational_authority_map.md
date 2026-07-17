# Estate Operational Authority Map

Status: WP-0688 repository-derived authority baseline
Campaign: CAMPAIGN-0681 — Estate Operationalization

This map summarizes canonical records for operational integration. It does not
grant authority. Where summaries conflict, the cited accepted charter, appointment,
campaign authorization, or explicit decision record prevails and the operation
fails closed.

## Authority matrix

| Actor / mechanism | May | Must route or stop for | Never gains through CAMPAIGN-0681 |
|---|---|---|---|
| Steward | set strategic direction and priority; decide protected constitutional, budget, privacy, exception and final institutional matters | Engineering architecture/technical review through Chief Architect; staffing evidence through Helen; routine coordination through offices | routine-scheduler obligation or implied decision from silence |
| Chief Architect | define Engineering architecture, decomposition and sequencing; review integration; release CAMPAIGN-0681 G1; make Engineering acceptance decisions where explicitly assigned | final/protected institutional, budget, staffing, privacy, deployment and other reserved decisions to their owners | Steward authority, automatic merge/deploy, or self-proving acceptance |
| Grace / Office of Operations | observe, recommend, coordinate delegated operations; create objectives/actions/checkpoints; request canonical Dispatch, staffing, validation and escalation | architecture/Engineering acceptance to Chief Architect; staffing to Helen; protected decisions to Steward; communication routing through Alfred where applicable | architectural, staffing, merge, deployment, Engineering-acceptance or final authority |
| Helen / HR | assess qualification, capability, availability and staffing; operate accepted personnel workflows | priority/architecture to Chief Architect or Steward; protected staffing/budget decisions to assigned authority | Engineering priority, architecture, Dispatch, merge or acceptance authority |
| Alfred / Chief of Staff | route and summarize communications; maintain duty/mailbox awareness; coordinate Steward attention | execution to Dispatch/providers; architecture to Chief Architect; staffing to Helen; protected decisions to Steward | executor, campaign state owner, validator or acceptance authority |
| Engineering workers | implement approved bounded packages and produce tests, evidence, commits and receipts | architecture/integration to Chief Architect; staffing to Helen; protected decisions to Steward | authority to approve own work or alter office powers |
| Codex / local models / providers | perform explicitly authorized mechanical execution within bounded paths and return evidence | ambiguous scope/authority, protected actions, gate release, merge/deploy/acceptance | officehood, decision authority, acceptance, staffing or spending authority |
| PTM / orchestrator / campaign executor | validate topology/readiness, project eligible work, execute authorized campaign mechanics and checkpoint | missing authority/evidence and protected gates to the named owner | independent priority, Dispatch, merge, deployment or acceptance authority |
| Dispatch / provider adapters | manage provider-neutral handoff and execution lifecycle after authorization | selection/authority/readiness failures to canonical owners | campaign priority, architecture, validation or acceptance authority |
| Validation / readiness | execute reproducible checks and report evidence-bound verdicts | failures/conflicts to package, integration or authority owner | power to merge, deploy, accept, or erase contradictory evidence |
| Mailboxes / messages / dashboards | communicate or present derived evidence | substantive decisions to the named office and canonical decision lane | status registry, approval, execution, or authority merely because an item was routed/viewed |

## Action-to-authority boundary

| Action kind | Required basis | Safe result when basis is absent or ambiguous |
|---|---|---|
| Observe | classification/access policy and canonical source reference | deny/redact or report unknown |
| Recommend | observation evidence, governing rule and named decision owner | advisory output only |
| Coordinate | explicit office authority or campaign delegation, bounded scope | stop and request the correct office |
| Request execution | eligible package/action, readiness evidence and canonical Dispatch mechanism | no queue mutation; report missing prerequisite |
| Mechanical action | explicit delegated policy naming actor, scope, side effects and stop conditions | refuse and escalate; technical capability is irrelevant |
| Office decision | exact office/officeholder authority evidence | requires review by that office |
| Protected decision | explicit Steward or other protected-authority decision | protected stop; silence is not consent |
| Acceptance | existing acceptance lane, exact object/commit/evidence and authorized accepter | remain completed/ready/awaiting review, never accepted |

## Controlling records and qualifications

- `docs/architecture/estate_operations_center_continuous_momentum_engine_architectural_charter.md`
  fixes Grace as operational owner, Chief Architect as Engineering authority, Alfred
  as router, Helen as staffing authority and Steward as final institutional authority.
- `operations/departments/engineering/engineering_department_charter.md` and the
  CAMPAIGN-0670 contracts govern Engineering, but their artifacts are only
  provisionally reusable under the bounded authorization until protected acceptance.
- `data/registry/personnel.json`, `data/registry/mailboxes.json` and appointment
  records resolve identity and routing; they do not independently define powers.
- WP-0678 authorizes bounded campaign execution but expressly withholds protected
  approval, merge, deployment, spending, staffing, disclosure and acceptance.
- The CAMPAIGN-0681 manifest and launch authorization permit implementation through
  WP-0690, then require a Chief Architect G1 release. They do not launch later work
  across G1 by implication.

## Evaluation rule for later packages

Every proposed action must identify the actor identity, institutional role, action
class, canonical target mechanism, authority evidence, prerequisites, side effects,
required decision owner and evidence to be produced. Missing or conflicting values
produce a refusal or `requires_review` disposition. WP-0690 may make this rule
machine-checkable but may not create an authority registry or broaden this map.
