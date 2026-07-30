# Canonical Capability-Discovery and Enablement Lifecycle

Status: Proposed contract; not implemented.

## Operating loop

```text
Grace objective
  -> required-capability decomposition
  -> Helen capability inquiry
  -> evidence-backed assessment
       -> available/qualified/healthy/authorized
            -> normal Engineering proposal -> approval -> PTM readiness -> Dispatch
       -> gap/unknown/unhealthy/unavailable/unauthorized
            -> capability-gap finding
            -> bounded Engineering specification consultation
            -> Helen capability-creation proposal
            -> separate enabling Engineering project
            -> normal approval/dependency/Dispatch/execution/validation/acceptance
            -> provider/adapter registration and evidence
            -> Helen re-evaluation
            -> Grace resumes original objective
```

Grace remains provider-agnostic. Helen owns workforce and qualification truth.
Engineering owns technical interpretation and approved capability creation.
Dispatch remains the execution handoff. Chief Architect and Steward authority
remains separate from completion, validation, and registration.

## States and ownership

| State | Owner | Meaning | Evidence |
|---|---|---|---|
| `capability_inquiry_requested` | Grace | Required capability set has been recorded for an objective. | Capability inquiry record linked to objective. |
| `capability_assessment_pending` | Helen | Helen has not yet evaluated current canonical evidence. | Inquiry plus source references. |
| `capability_available` | Helen | All required capabilities are qualified, healthy, available, and authorized for scope. | Assessment with worker, qualification, health, availability, authorization references and observation times. |
| `capability_unknown` | Helen | Evidence is absent, stale, ambiguous, or conflicting. | Assessment with missing/stale/conflict reasons. |
| `capability_gap_found` | Helen | Required capability is absent or cannot satisfy constraints. | Gap finding and remaining capability set. |
| `specification_consultation_requested` | Helen | Engineering is asked only to define a technical worker/capability specification. | Advisory consultation record; no project or Dispatch authorization. |
| `capability_creation_proposed` | Helen | Helen proposes a worker capability with boundaries, qualifications, and validation. | Capability-creation proposal. |
| `enabling_project_proposed` | Grace | Grace creates a separate normal Engineering project linked to the original objective. | Grace objective/action plus project/dependency references. |
| `enabling_project_waiting` | PTM/orchestrator | Dependencies, authority, staffing, or readiness are incomplete. | PTM readiness/dependency record. |
| `enabling_project_in_progress` | Engineering/Dispatch | Approved enabling project is executing through normal handoff. | Dispatch, adapter, provider, artifact, validation records. |
| `capability_registration_pending` | Engineering | Work product exists but registration evidence is incomplete. | Registration result with missing evidence. |
| `capability_registered_pending_reevaluation` | Helen | Technical registration exists; workforce qualification/health/availability must be checked. | Registration result plus re-evaluation request. |
| `original_project_resumable` | Grace | Helen has confirmed the original dependency is satisfied. | Re-evaluation and dependency-satisfaction record. |
| `original_project_resumed` | Grace/PTM | Original objective continues without repeated Steward intake. | New linked readiness/Dispatch attempt, not a mutated prior record. |
| `blocked` / `failed` / `superseded` | Owning authority | A safe continuation is unavailable or the proposal is replaced. | Explicit reason, owner, recovery or supersession reference. |

## Capability assessment decision rule

For each required capability, Helen evaluates separate facts:

`declared -> qualified -> healthy -> available -> authorized`.

The aggregate result is `capability_available` only when every required
capability has affirmative, fresh evidence for the same worker/provider/adapter
scope. A recommendation is not a selection; a provider catalog entry is not a
qualification; a healthy service is not an authorized worker; a worker identity
is not an adapter implementation.

## Engineering specification consultation

Helen may send a bounded advisory request through the existing repository
message/mailbox or campaign operation surface. The consultation must include:

- original objective and required capability IDs;
- observed gap and constraints;
- known bootstrap capabilities;
- requested output schema;
- statement that the response cannot authorize implementation or execution;
- return recipient and evidence deadline.

Engineering returns a worker specification, assumptions, prohibited claims,
qualification tests, health checks, adapter expectations, artifact/receipt
contract, cancellation behavior, and bootstrap dependencies. It does not create
an enabling project or Dispatch item as part of consultation.

## Enabling-project dependency and resumption

The original objective retains its immutable identity. The enabling project gets
its own project/work-package/attempt/Dispatch identities and records
`enables_capability_gap_id`. A PTM dependency links:

`original_objective -> required_capability -> gap -> enabling_project -> registration_result -> re_evaluation`.

The original objective moves to a waiting state with a durable dependency
reference. On successful re-evaluation, Grace creates a new linked readiness and
Dispatch attempt. No historical objective, request, or failed Dispatch record
is overwritten. If re-evaluation still finds a gap, the original remains
blocked and a new evidence-backed action is proposed.

## Recursion/bootstrap rule

An enabling project may use only capabilities independently evidenced before the
gap: for example repository access, deterministic tests, documentation,
approved code execution, or an existing image-processing tool. It may not count
the capability it is creating as a bootstrap dependency. If the specification,
implementation, validation, or registration requires a missing bootstrap
capability, Helen records a second gap and the enabling project is blocked or
re-scoped; no recursive self-claim is permitted.

## Completion boundaries

Provider/adapter execution completion, Engineering validation, capability
registration, Helen re-evaluation, Grace resumption, Chief Architect acceptance,
and Steward acceptance remain distinct. A registration result cannot itself
authorize provider execution, and a successful enabling project cannot silently
accept the original project.
