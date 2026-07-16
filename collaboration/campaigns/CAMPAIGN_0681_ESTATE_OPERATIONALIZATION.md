# CAMPAIGN-0681 — Estate Operationalization

Status: Draft — not launched  
Parent authority: Steward direction to operationalize the Estate after campaign-level execution capability is available  
Architecture and acceptance owner: Chief Architect  
Operational owner: Grace, within existing authority boundaries  
Priority: High  
Risk class: Elevated — cross-office operational integration without authority transfer

## Approved intent

- Intake source kind: Steward directive
- Canonical intake reference: Steward direction during Chief Architect planning discussion, following CAMPAIGN-0670 and WP-0678 review
- Disposition decision: Proceed with one large, dependency-aware operationalization campaign rather than another documentation-only institutional-foundation campaign

## Objective and outcomes

Make the Estate behave as an operating institution rather than a collection of individually functional systems.

The campaign shall connect existing offices, residents, services, campaigns, work packages, mailboxes, health signals, staffing, validation, escalation, continuity, and Steward review into one observable and governed operational flow.

CAMPAIGN-0681 shall be intentionally broad at campaign level while preserving atomic work-package boundaries. It is intended to become the first substantial institutional campaign executed through the campaign-level Codex execution capability established by WP-0678.

Successful completion means:

1. one approved campaign handoff can initiate the campaign;
2. Grace can observe and coordinate operational momentum without acquiring protected authority;
3. Helen can supply staffing and capability through explicit requests and evidence;
4. Alfred can route operational communications without becoming the execution authority;
5. Engineering can operate as one department within the larger Estate operating model;
6. resident and service health can affect campaign readiness and escalation truthfully;
7. campaigns can advance, pause, resume, block, recover, and close through repository-grounded state and evidence;
8. the Steward receives concise, decision-ready operational views and protected escalation requests;
9. all automated or assisted actions remain bounded by existing institutional authority;
10. the campaign closes through one campaign pull request and protected acceptance process.

## Constitutional precedence

Existing accepted Estate constitutional, office, campaign, engineering, communication, mailbox, PTM, Dispatch, validation, readiness, evidence, acceptance, reflection, and continuity standards remain authoritative.

If an apparent conflict exists between this campaign and an accepted canonical artifact, the accepted canonical artifact shall prevail.

CAMPAIGN-0681 is authorized to connect and operationalize existing systems. It shall not silently redefine, replace, supersede, or transfer established authority. Any required constitutional or office-authority change must be isolated as a protected architectural decision and approved separately.

## Required authoritative inputs

Before decomposition or execution, discover and read the canonical successors of at least:

- `AI_HINTS.md`
- `AI_START_HERE.md`
- `AI_COMMUNICATION_HINTS.md`
- `collaboration/campaigns/CAMPAIGN_0670_ACCEPTANCE_PACKAGE.md`
- all WP-0670 through WP-0675 completion receipts and accepted deliverables
- `collaboration/work_packages/pending/WP-0678_Campaign_Level_Codex_Execution_Capability.md` and its eventual completion evidence
- existing office charters for Grace, Helen, Alfred, Chief Architect, and Steward
- canonical PTM, Dispatch, mailbox, repository-message, resident, service-health, validation, readiness, acceptance, reflection, and continuity specifications
- CAMPAIGN-0680 artifacts where decision-support outputs or dashboards overlap

A moved path is not permission to invent a replacement. Discover the canonical successor through repository evidence.

## Scope

The campaign includes implementation, integration, validation, and bounded documentation necessary to establish:

- a canonical Estate operational state model;
- operational event ingestion and normalization from existing systems;
- campaign and work-package momentum observation;
- dependency, readiness, health, staffing, validation, and authority-aware coordination;
- resident and service health integration;
- operational blocker classification and escalation;
- explicit office interaction contracts expressed through existing mechanisms;
- staffing and capability request flows;
- communication and mailbox routing integration;
- pause, resume, retry, recovery, and fail-closed behavior;
- operational dashboards and Steward decision surfaces;
- durable evidence, auditability, notebook, reflection, and continuity integration;
- a bounded Continuous Momentum Engine capability that recommends or performs only actions already authorized by canonical policy;
- pilot execution using a real but bounded institutional workflow;
- campaign-level acceptance evidence.

## Non-goals and protected surfaces

This campaign shall not:

- create a new office or department when an existing office can own the function;
- transfer final authority away from the Steward;
- grant Grace architectural, staffing, engineering-acceptance, merge, deployment, or final institutional authority;
- grant Helen engineering priority, architectural, or acceptance authority;
- grant Alfred execution or acceptance authority;
- treat Codex, a local model, or any provider as an office or institutional authority;
- bypass PTM, Dispatch, mailbox, repository-message, validation, readiness, evidence, or acceptance mechanisms;
- create duplicate registries, queues, schedulers, validators, dashboards, or state stores where canonical systems can be extended;
- silently merge, deploy, accept, or close protected work;
- conceal degraded residents, services, stale evidence, failed validation, blocked authority, or partial campaign failure;
- replace CAMPAIGN-0670 engineering standards or CAMPAIGN-0680 decision-support capabilities;
- build an unconstrained autonomous agent loop.

## Campaign execution policy

After WP-0678 is accepted and operationally authorized, CAMPAIGN-0681 shall use:

- one campaign handoff;
- one campaign branch;
- one bounded commit per atomic work package;
- dependency-aware execution;
- explicit approved parallel groups only where shared-file and authority safety is proven;
- durable checkpoints and resumability;
- fail-closed partial-failure handling;
- aggregated campaign evidence;
- one campaign pull request;
- no automatic merge or acceptance.

The campaign shall not launch before WP-0678 completion evidence and Chief Architect launch approval exist.

## Proposed work-package graph

The following is the authorized decomposition target. Package numbers are reserved for this campaign beginning after CAMPAIGN-0680's WP-0680 through WP-0687 range.

| Package ID | Objective | Depends on | Integration checkpoint |
|---|---|---|---|
| WP-0688 | Estate operational current-state and canonical-reuse map | none | G1 |
| WP-0689 | Operational state, event, and transition contract | WP-0688 | G1 |
| WP-0690 | Authority-aware operational action taxonomy | WP-0688, WP-0689 | G1 |
| WP-0691 | Resident and service health signal integration | WP-0688, WP-0689 | G2 |
| WP-0692 | Campaign and work-package momentum observer | WP-0688, WP-0689 | G2 |
| WP-0693 | Operational blocker and escalation classifier | WP-0690, WP-0691, WP-0692 | G2 |
| WP-0694 | Grace operational coordination surface | WP-0690, WP-0692, WP-0693 | G3 |
| WP-0695 | Helen staffing and capability request integration | WP-0690, WP-0693 | G3 |
| WP-0696 | Alfred communication and mailbox routing integration | WP-0690, WP-0693 | G3 |
| WP-0697 | Engineering Department operational integration | WP-0692, WP-0693, WP-0694 | G3 |
| WP-0698 | Readiness, validation, and evidence signal unification | WP-0691, WP-0692, WP-0697 | G4 |
| WP-0699 | Operational pause, resume, retry, and recovery controls | WP-0693, WP-0698 | G4 |
| WP-0700 | Continuous Momentum Engine bounded decision loop | WP-0694, WP-0698, WP-0699 | G5 |
| WP-0701 | Authorized action adapters using existing institutional seams | WP-0695, WP-0696, WP-0697, WP-0700 | G5 |
| WP-0702 | Operational checkpointing, audit, and replay evidence | WP-0698, WP-0699, WP-0700 | G5 |
| WP-0703 | Steward operational dashboard and protected decision queue | WP-0693, WP-0698, WP-0702; reuse CAMPAIGN-0680 | G6 |
| WP-0704 | Metrics, notebook, reflection, and continuity integration | WP-0702, WP-0703 | G6 |
| WP-0705 | Failure-mode, authority-boundary, and degraded-service validation | WP-0700, WP-0701, WP-0702, WP-0703 | G7 |
| WP-0706 | Bounded real-work pilot campaign | WP-0705 | G7 |
| WP-0707 | Estate Operationalization integration and acceptance package | all prior packages | G8 |

Every work package shall name CAMPAIGN-0681 as its one primary campaign and shall preserve independently readable completion evidence.

## Milestones and integration gates

| Gate | Prerequisites | Evidence | Release authority |
|---|---|---|---|
| G0 — Launch authorization | WP-0678 accepted; campaign manifest complete; branch/base verified | WP-0678 receipt, campaign hash, readiness evidence | Chief Architect and Steward where protected |
| G1 — Canonical and authority freeze | WP-0688 through WP-0690 | reuse map, state/event contract, action taxonomy, conflict report | Chief Architect |
| G2 — Observation truth | WP-0691 through WP-0693 | health, momentum, blocker and escalation tests | Chief Architect |
| G3 — Office integration | WP-0694 through WP-0697 | office interaction proofs; no authority transfer | Chief Architect plus office acknowledgements where required |
| G4 — Governed control readiness | WP-0698 and WP-0699 | readiness/evidence integration and recovery proof | Chief Architect |
| G5 — Momentum capability | WP-0700 through WP-0702 | bounded-loop, adapter, checkpoint, replay, and fail-closed evidence | Chief Architect; Steward approval for protected action classes |
| G6 — Steward visibility and continuity | WP-0703 and WP-0704 | dashboard, decision queue, metrics, notebook, reflection, continuity evidence | Steward review |
| G7 — Safety and pilot proof | WP-0705 and WP-0706 | failure-mode report, authority-boundary proof, pilot receipts | Chief Architect and Steward |
| G8 — Campaign acceptance | WP-0707 | aggregate evidence, PR, unresolved blockers, acceptance package | Protected acceptance lane; no automatic acceptance |

## Required behavioral model

The resulting operational flow must support this bounded pattern:

1. Observe canonical state and new events.
2. Reconcile state against campaign dependencies, readiness, health, evidence, staffing, and authority.
3. Identify eligible, blocked, degraded, failed, or protected work.
4. Recommend the next authorized action and explain why.
5. Perform only actions explicitly delegated to the acting office or adapter.
6. Stop at review, acceptance, merge, deployment, budget, privacy, staffing, architectural, or Steward gates as canonical policy requires.
7. Record every recommendation, action, refusal, transition, failure, retry, and escalation.
8. Resume deterministically from the last safe checkpoint.

The system must distinguish clearly among:

- observation;
- recommendation;
- coordination;
- execution request;
- authorized mechanical action;
- office decision;
- protected institutional decision;
- acceptance.

No recommendation or mechanical action may be misrepresented as authority or acceptance.

## Shared-file collision plan

The final work-package definitions and machine-readable manifest must identify exact owned paths and shared-file rules before launch.

At minimum:

- canonical registries and office charters are read-only unless a separately approved package grants modification authority;
- shared operational state and dashboard surfaces must be integrated through designated integration packages;
- WP-0707 owns final campaign aggregation and acceptance-package updates;
- packages touching the same runtime seam must be sequenced unless the manifest proves collision-free parallel execution;
- no package may rewrite another package's completion receipt.

## Pilot requirement

WP-0706 shall run one real but bounded workflow that crosses multiple existing Estate capabilities. The pilot must prove, at minimum:

- a campaign or governed initiative is observed from canonical state;
- readiness, dependency, resident/service health, staffing, validation, and authority are evaluated;
- Grace receives a coordination view;
- Helen and Alfred are engaged only through their existing lanes;
- Engineering receives executable work through its accepted mechanisms;
- one interruption or failure is recovered from a durable checkpoint;
- one protected decision is escalated and not bypassed;
- Steward visibility is concise and evidence-backed;
- completion evidence remains package- and campaign-readable;
- no automatic merge, deployment, or institutional acceptance occurs.

## Acceptance criteria

CAMPAIGN-0681 is complete only when the Estate can truthfully demonstrate an end-to-end operational cycle in which existing institutional systems cooperate as one governed operating model.

Acceptance requires proof that:

- the campaign ran through the WP-0678 campaign-execution capability;
- existing canonical systems were reused rather than duplicated;
- operational state is repository-grounded, observable, and auditable;
- Grace can coordinate momentum without acquiring protected authority;
- Helen, Alfred, Engineering, residents, and services participate through their proper lanes;
- dependency, readiness, health, validation, evidence, staffing, and authority affect progression correctly;
- interruption and partial failure are recoverable;
- protected gates stop unauthorized continuation;
- the Steward receives decision-ready operational information;
- one bounded pilot completed with truthful evidence;
- one campaign PR presents the complete change set;
- no merge, deployment, or acceptance occurred automatically.

## Required deliverables

The campaign shall ultimately produce:

1. one canonical campaign execution manifest compatible with WP-0678;
2. atomic pending work packages WP-0688 through WP-0707;
3. implementation and tests in existing canonical seams;
4. per-package completion receipts;
5. gate evidence and authority decisions;
6. failure-mode and degraded-service validation reports;
7. pilot evidence;
8. operational documentation sufficient for Grace, Helen, Alfred, Engineering, Chief Architect, and Steward use;
9. campaign aggregate evidence;
10. `collaboration/campaigns/CAMPAIGN_0681_ACCEPTANCE_PACKAGE.md`;
11. one campaign pull request for protected review.

## Amendment history

| Version/time | Action | Decision authority/reference | Affected packages and reevaluation |
|---|---|---|---|
| Draft 1 | Initial campaign charter created from Steward direction | Steward direction; Chief Architect drafting | Entire campaign remains unlaunched pending WP-0678 acceptance, detailed decomposition, staffing, readiness, and launch review |
