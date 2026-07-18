# Estate Operational Action Taxonomy

Status: WP-0690 implementation contract
Schema version: `estate.operational.action.v1`
Campaign: CAMPAIGN-0681 — Estate Operationalization

## Purpose and non-authority boundary

This taxonomy classifies proposed actions before they reach canonical PTM,
Dispatch, office runtime, repository-message, validation, merge, deployment,
protected-decision, or acceptance seams. It evaluates supplied identity, scope,
authority, readiness, validation and evidence references. It does not resolve an
identity from a title, grant authority, persist a decision, execute an action, or
create an office, authority registry, queue, scheduler, dispatcher, or acceptance
system.

Canonical constitutional, office, appointment, campaign and mechanism records
remain controlling. The matrix below is a fail-closed policy derived from them, not
a source of authority.

## Action classes

| Class | Meaning | Required canonical mechanism | Side effect boundary |
|---|---|---|---|
| `observe` | Read a canonical source | `canonical_source_read` | none |
| `recommend` | Produce evidence-backed advice for a named owner | `office_decision_support` | advisory only |
| `coordinate` | Organize or route work inside an existing office scope | `office_runtime_or_repository_message` | routing only |
| `request_execution` | Submit eligible work to governed execution | `execution_dispatch` | request, not execution |
| `mechanical_action` | Perform an explicitly delegated bounded action | `delegated_target_adapter` | bounded write with outcome evidence |
| `office_decision` | Record a decision inside a named office's scope | `canonical_office_record` | office decision record only |
| `protected_decision` | Request a decision from protected authority | `protected_authority_record` | always stops for human/office review |
| `acceptance` | Request formal acceptance in an existing lane | `existing_acceptance_lane` | always stops; never inferred |

Each class has a unique mechanism and side-effect signature, preventing an advisory
or routing record from masquerading as a decision or execution result.

## Descriptor and evaluation contract

The machine-readable schema is
`schemas/operations/estate_operational_action_v1.schema.json`; the implementation is
`src/estate/core/operational_action_taxonomy.py`. A descriptor includes the action
class/ID, evidence-bound actor and role, source state/event references, canonical
target/mechanism, required authority and evidence, readiness/validation/evidence
requirements, side effects, protected surfaces, idempotency/retry policy,
stop/escalation conditions, disposition, and later decision/execution evidence.

`evaluate_action` returns classification, `allowed`, `denied`, or
`requires_review`, authoritative basis, missing prerequisites, required mechanism,
decision owner, stop/escalation flag, evidence to produce, next safe action, and an
explanation. Missing identity, unknown role, ambiguous scope, conflicting authority,
or incomplete prerequisites fails closed. `allowed` only means the proposal may be
carried by its declared canonical mechanism; it is not approval of downstream
execution, merge, deployment, protected action, or acceptance.

## Office boundary mapping

| Actor | Evidence-bound allowed scope | Explicit boundary |
|---|---|---|
| Grace | observation, recommendation and operational/recovery coordination; eligible execution requests through Dispatch | no architecture, staffing decision, Engineering acceptance, merge, deployment, or final authority |
| Helen | staffing, capability and workforce coordination/office decisions | no Engineering priority, architecture, Dispatch execution, or acceptance |
| Alfred | communication routing and Chief-of-Staff coordination | routing is not execution, source state, validation, or acceptance |
| Chief Architect | Engineering architecture, coordination, integration and Engineering acceptance in the named lanes | no automatic merge/deploy, staffing, budget, or final institutional authority |
| Steward | strategic, institutional, budget, privacy, constitutional and final protected decisions | protected records still require the existing decision lane; silence is not consent |
| Engineering worker | bounded Engineering execution requests/mechanics under package authority | cannot approve own work or acquire office authority |
| Codex/local model/provider | explicitly delegated bounded mechanical execution | provider identity/capability is never office, decision, staffing, spending, or acceptance authority |

The evaluator requires identity and action-specific authority evidence even where a
role appears in this table. Personnel/mailbox metadata identifies routing targets;
it does not independently prove powers.

## Protected surfaces and fail-closed ownership

Engineering architecture and Engineering acceptance route to the Chief Architect;
staffing routes to Helen or the explicitly named protected staffing authority;
constitutional and final institutional acceptance route to the Steward. Budget,
spending, privacy, merge, deployment and disclosure route to the explicit authority
named by their canonical policies. The evaluator never performs protected decisions
or acceptance, even when evidence exists; it returns `requires_review` and the
correct owner.

## Narrow integration guidance

Later CAMPAIGN-0681 adapters should call `evaluate_for_mechanism` immediately before
submitting to the named canonical seam. A mismatch between caller and descriptor
mechanism is denied. An allowed recommendation stays advisory; an allowed Dispatch
request stays a request; an allowed mechanical action must carry explicit delegation
and produce validation/evidence; provider success stays separate from office
decision and acceptance. Mail routing must retain canonical state references but
cannot change that state by itself.

This package does not implement Grace, Helen, or Alfred surfaces or the Continuous
Momentum Engine. It supplies only their shared preflight vocabulary.
