# Engineering Campaign Intake Contract

Status: Gate B contract
Campaign: CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION
Work package: WP-0671
Authority owner: Chief Architect

## Purpose and boundary

This contract converts already-governed intent into an Engineering campaign without creating an Engineering inbox, approval queue, planning registry, scheduler, or dispatch path. PTM/orchestrator intake records remain canonical; `collaboration/campaigns/` and `collaboration/work_packages/` are the repository definitions. A campaign document is a governed projection of an approved source, not approval by itself.

## Accepted intake sources

Every intake record MUST reference one canonical source and its stable identifier, path or URI, version/digest, disposition, decision actor, authority basis, and decision time.

| Source kind | Minimum evidence before Engineering planning | Approval authority |
|---|---|---|
| idea or discovery | PTM/orchestrator intake record; problem and provenance | Intake authority records `discover`, `hold`, or `reject`; it cannot approve architecture |
| accepted proposal | accepted proposal and decision record | authority named by the proposal process |
| architectural decision | accepted ADR/architecture record and constraints | Chief Architect |
| defect | reproducible defect record, affected asset and severity | designated intake authority; protected remediation still needs its protected approval |
| operational blocker | canonical incident/blocker record, impact and owner | operational authority for triage; Chief Architect for Engineering scope |
| Steward directive | durable directive record and authority basis | Steward; Chief Architect still owns Engineering architecture and acceptance |

Messages, meetings and notebooks may point to an intake source but are not state. An unrecorded request is returned for canonical intake.

## Disposition state machine

- **Discovery:** the problem, value, authority, or feasible boundary is unresolved. Discovery may produce evidence, never execution authorization.
- **Planning package:** approved investigation or bounded design work is needed, but coordinated implementation is not yet justified. It has an owner, acceptance evidence and a canonical package ID.
- **Engineering campaign:** approved intent requires two or more coordinated packages, a dependency/integration graph, or campaign-level acceptance. The Chief Architect accepts its architecture and charter before execution readiness can pass.
- **Rejected:** out of authority, unsafe, conflicting, duplicative, or unsupported. Record reason and actor; do not delete the source.
- **Held:** potentially valid but awaiting evidence, priority, funding, staffing, dependency, or protected decision. Record review trigger and owner.

Transition evidence is append-only or superseding; a status label or directory move alone is insufficient. Rejection and hold do not mint executable work. One intake source may inform multiple campaigns, but each campaign names one primary parent-authority record and explains other references.

## Campaign contract

A campaign definition MUST contain:

- literal `campaign_id`, unique under the existing campaign convention;
- `parent_authority_ref` (stable ID, artifact path/URI, digest/version, actor, decision time);
- Chief Architect as architecture/Engineering-acceptance owner, plus operational owner where different;
- priority and the authority/evidence supporting it;
- bounded scope, explicit non-goals and protected surfaces;
- milestones and named integration gates;
- acyclic package dependency graph with typed edges;
- risk class (`standard`, `elevated`, `protected`) and rationale;
- acceptance lane, acceptance actor and required completion evidence;
- amendments and supersession links.

Every package has exactly one `primary_campaign_id`. Cross-campaign dependencies are references, not dual membership. Campaign and package IDs are preserved in staffing, PTM readiness, scheduling, Dispatch, execution attempt, validation, PR, receipt and continuity evidence.

## Authority and handoff

The Chief Architect accepts Engineering architecture, decomposition exceptions, integration gates and final Engineering acceptance. PTM/orchestrator records eligibility and schedule state; it does not replace architectural acceptance. Helen provides staffing/capability evidence; Grace coordinates checkpoints and escalation; Alfred routes notices; providers execute only bounded Dispatch handoffs. None of these roles may infer acceptance.

An intake is handed to decomposition only when its source and disposition are durable, parent authority is valid, owner and acceptance authority are named, and scope can be bounded. Otherwise it fails closed to discovery or hold.

## Lifecycle changes

All changes preserve the old charter and add a dated decision record:

- **Amend:** Chief Architect approves changed scope, graph, risk, evidence or acceptance; affected packages return to readiness evaluation and material post-validation changes invalidate old evidence.
- **Pause:** authorized owner records reason, safe-stop requirements, branch/reservation disposition and resume conditions. Pause is not cancellation or acceptance.
- **Cancel:** parent authority or Chief Architect records authority, reason, cleanup/rollback and evidence retention. In-flight Dispatch is stopped through its canonical control, not this document.
- **Supersede:** replacement campaign/package names predecessor and migration/disposition for every open package, branch and artifact.
- **Replan:** dependency, estimate, provider or validation changes receive a new plan version; acceptance-required changes require Chief Architect approval.

No lifecycle action rewrites historical receipts or silently releases branch ownership.
