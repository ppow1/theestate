# GRC-002 — Grace Cognition and Escalation Contract

Status: Canonical specification proposal — read-only architecture task  
Version: 1.0.0  
Date: 2026-08-25  
Scope: resident cognition tiers, escalation, provider/resource binding, and provenance

## 1. Purpose and invariants

This document specifies Grace’s multi-tier cognition contract. It does not
change runtime code, create migrations, assign models, implement routing, or
alter the current Grace runtime.

The governing identity invariant is:

Office != Occupant != Implementation != State

Grace is one occupant. Home cognition, high reasoning, and external reasoning
are replaceable implementations/providers for that occupant, not different
Graces. Hardware, model, runtime endpoint, provider, GPU, session, and context
are implementation metadata, never identity.

Deterministic CME behavior is also separate. State machines, polling, leases,
dependency progression, retries, bookkeeping, known transitions, and
capacity accounting are not Grace reasoning unless a real Grace cognition event
generated the judgment.

## 2. Existing architecture findings

### Verified foundations

The [resident localization roadmap](Riverview/docs/architecture/riverview_resident_localization_master_roadmap.md)
defines Office/Occupant/Implementation/State separation, a reusable substrate,
resident-specific cognition/authority patterns, and the distinction between
cognitive and operational escalation. The [Riverview Charter](Riverview/docs/governance/RIVERVIEW_CHARTER.md)
and [Engineering Interaction Contract](Riverview/docs/operations/RIVERVIEW_ENGINEERING_INTERACTION_CONTRACT.md)
establish local-first reasoning, provider neutrality, bounded authority,
event-first state, capacity-aware work, and Steward escalation by exception.

Riverview/src/riverview/residents/runtime.py has separate
ImplementationBinding, RuntimeSession, ResidentImplementationRuntime, and
ResidentTransitionRuntime types. Transitions preserve the occupant,
preflight rehydration, retire the old binding, and record provenance. The
focused runtime tests prove binding/session identity separation and
implementation replacement continuity.

Riverview/src/riverview/residents/context.py builds bounded,
provenance-aware ContextBundle objects with identity, office, authority,
assignment, classifications, evidence references, dependency fingerprints,
exclusions, and audit provenance. It preserves contradictions as unresolved,
rejects stale bundles, and explicitly says implementation/provider/model/host
are not occupant identity. This is the correct source seam for a reasoning
packet, but it is not itself cognition orchestration.

Riverview/src/riverview/reasoning/contracts.py provides bounded,
provider-neutral ReasoningProvider, ReasoningRequest, and ReasoningResponse
envelopes with correlation, classification, expiry, evidence requirements,
advisory authority, and bounded output. The registry filters by health,
capacity, and classification. Ollama and llama.cpp adapters are loopback-only.

Riverview/src/riverview/residents/runtime.py also has
CognitiveEscalationRuntime: healthy eligible adapters receive bounded
advisory requests; correlation and classification are checked; no institutional
authority is granted. Its current request is generic bundle/reference context,
not the home-to-high packet in this contract.

The Estate Grace consultation/CME evidence proves useful partial behavior:
logical consultation identity, bounded context, capacity reservation, held
work, lease recovery, correlated responses, no fabricated completion, and
Steward-required outcomes after bounded attempts. The governed scheduler proves
idempotent queueing, priority order, health exclusion, reservation expiry, and
that reservation does not dispatch.

### Verified gaps

The repository does not yet prove a first-class home/high cognition policy.
Current resident runtime sessions are explicitly non-cognitive. Current
reasoning responses do not identify a cognition tier or contain the required
decision/rationale/uncertainty/further-escalation structure.

LocalGpuReasoningAdapter closes adapter IDs to rtx4090 and p100; it is a GPU
probe, not a resident/provider/resource abstraction and does not represent the
3060-class home tier. The current Grace local-model evidence in
docs/operations/reviews/ESTATE_Grace_Local_Model_Provenance_20260808.md proves
one real Ollama generation and explicitly records bootstrap fallback, not an
accepted Grace model assignment or multi-tier routing policy.

Shared-resident identity isolation, queue fairness, model residency,
concurrency, and latency policy are extension requirements, not currently
proven behavior. Existing mechanisms must not be called compliant merely
because they contain similarly named fields.

## 3. Canonical cognition tiers

### Tier 0 — Deterministic substrate

Applies known state transitions: polling, leases, dependency checks, retries
under an existing policy, bookkeeping, capacity, idempotency, evidence
indexing, and status projection. It may return known mechanical states such as
waiting, held_for_capacity, retry_scheduled, blocked, or indeterminate. It
must not resolve novel intent, weigh material tradeoffs, or claim resident
judgment.

### Tier 1 — Home cognition

Grace’s responsive, continuous operational cognition, primarily hosted by the
RTX 3060 Ti 8 GB class resource. It performs routine CME oversight, ordinary
classification/routing recommendations, monitoring of work/evidence, bounded
operational interpretation, and recognition that stronger reasoning is needed.
It owns the first cognition decision for an eligible request and may make a
delegated routine recommendation or emit an escalation request.

The 3060 and final home model are capability/resource configuration, not
identity. Queue wait, admission, load, generation, and end-to-end latency must
be recorded; concrete SLOs remain a Steward decision.

### Tier 2 — High reasoning

Stronger local reasoning, primarily available on the RTX 4090 24 GB class
resource and capable of an approximately 3032B-class implementation. The
number is a capability target, not a fixed model name. High reasoning is
invoked only after home cognition records why the question exceeds home
reliability. It receives a bounded packet and returns a typed recommendation/
decision, rationale, confidence or uncertainty, constraints, unresolved
questions, and whether further escalation is warranted.

High reasoning remains the same Grace occupant. It cannot execute, merge,
accept, appoint, spend, alter authority, or mutate canonical identity.

### Tier 3 — External cognitive escalation

Approved external advisory reasoning for a bounded, classified packet. It does
not become Grace, acquire institutional authority, access unapproved data,
execute, or bypass acceptance paths. Provider identity, request/response
correlation, classification, availability, and bounded contribution are
mandatory. The current Riverview prohibition on OpenAI API model routes
remains in force unless separately revised.

### Tier 4 — Steward escalation

Human judgment for authority, acceptance, protected boundaries, material
ambiguity, unsafe recovery, policy exceptions, identity/office changes, or
persistent tier disagreement. It is not a model/provider tier.

## 4. Responsibility and authority matrix

| Actor | May do | Must not do | Authority of output |
|---|---|---|---|
| Deterministic substrate | Apply declared mechanics and record state | Resolve novel/material ambiguity or claim resident judgment | Mechanical transition |
| Grace home cognition | Routine classification, evidence monitoring, coordination, escalation detection | Silent tier/provider switch; authority expansion; masquerading mechanics | Grace recommendation within policy |
| Grace high reasoning | Bounded difficult analysis and recommendation | Execute, accept, merge, redefine identity/authority | Grace decision proposal/advisory result |
| External provider | Independent bounded advice | Acquire Grace identity/authority or execute | External advisory only |
| CME/orchestrator | Queue, reserve, wake, reconcile, retry under policy | Convert scheduling into resident judgment | Deterministic orchestration event |
| Codex/worker | Authorized bounded action and evidence | Expand scope or speak as Grace | Execution evidence |
| Engineering validation | Defined checks and pass/fail evidence | Approve architecture/merge/acceptance | Validation evidence |
| Steward | Constitutional/material decisions and acceptance | — | Steward decision/acceptance |

## 5. Escalation decision contract

For every cognition-eligible request, home cognition records one of:
DETERMINISTIC, HOME_DECISION, HIGH_REASONING_REQUIRED,
EXTERNAL_ADVISORY_REQUIRED, or STEWARD_REQUIRED. Tier 0 itself emits a
deterministic event, not a resident decision event.

The record contains: decision ID; resident/occupant/office IDs; current
implementation ID; objective/correlation; decision class and reason code;
question; authoritative state and evidence refs; constraints; classification;
policy version; timestamp/expiry; next tier; and provenance.

Deterministic examples: an expired lease returns to queue under the documented
rule; an incomplete dependency remains waiting; a duplicate key returns the
existing result. It is incorrect for deterministic logic to choose between
materially different recovery strategies or resolve conflicting current
evidence.

Home examples: classify an accepted item into a known lane; summarize current
progress and identify the dependency-ready waypoint; recognize that a defined
validation artifact satisfies a defined requirement; route a routine notice.

High-reasoning examples: select between safe but materially different recovery
strategies; reconcile conflicting continuity evidence without changing
identity; evaluate a novel resource policy or consequential architecture
tradeoff. Home must state why its reliable capability is exceeded.

External examples: obtain an independent critique of a bounded architecture
recommendation using nonprotected evidence, or request a second opinion when
local high reasoning is unavailable and policy permits it. A second-opinion
phrase does not itself authorize bypassing policy.

Steward examples: accept an authority-model change, decide whether protected
data may leave local processing, accept a new canonical implementation, or
resolve persistent material disagreement.

## 6. Bounded reasoning packet and return path

The home-to-high/external handoff is a versioned ResidentReasoningPacket,
assembled from authoritative state and relevant evidence. It is not a full
conversation dump.

Required fields:

packet_version, packet_id, resident_id, occupant_id, office_id,
source_cognition_event_id, objective_id, correlation_id, exact_question,
objective, authoritative_current_state, constraints, relevant_evidence,
unresolved_ambiguity, relevant_prior_decisions, known_deterministic_results,
home_assessment, requested_output_schema, classification, egress_policy,
expiry, and max_budget.

Optional fields include relevant relationships, prior high-tier results, and
latency/resource constraints. Unrelated history, secrets, unapproved protected
payloads, hidden prompts, and unrelated resident memory are forbidden by
default. Omitted context must be represented by an omission reason when its
absence affects confidence.

The return envelope contains response/request/correlation IDs; resident,
occupant, implementation, provider, and resource IDs; recommendation/decision;
rationale; confidence/uncertainty; observed constraints; unresolved questions;
further-escalation flag; evidence refs; classification; and created/expiry
times.

After a valid result, home Grace resumes operational coordination. The result
remains advisory reasoning evidence and does not become execution or acceptance
authority.

## 7. Provider/resource binding contract

The reusable abstraction is:

ResidentPolicy -> CognitionTierBinding -> ProviderBinding
  -> ResourceBinding -> ImplementationBinding -> ModelCapabilityProfile

A binding identifies resident/occupant/office, tier and purpose, implementation
version, provider adapter/type, capability profile, resource class/host/GPU
class, locality, classification/egress eligibility, context/output limits,
structured-output capability, concurrency/capacity, health/freshness,
latency/timeout, predecessor binding, policy version, and authorization/
provenance references.

Model names, quantization, runtime, endpoints, and final GPUs are configuration
records. Replacement creates implementation/binding history but does not alter
identity or orchestration logic. A GPU is a resource candidate, not a Grace
assignment.

Selection must filter capability, classification, health, capacity, and policy.
Recommendation, authorized selection, reservation, dispatch, adapter handoff,
live confirmation, and result are separate events. A recommendation never
selects itself; a reservation never dispatches itself.

## 8. Shared-resident home-resource requirements

The 3060-class service must eventually support multiple residents:

- Every request, queue item, session, packet, cache, and result is keyed by
  resident/occupant, office, implementation, and correlation IDs.
- Context bundles are isolated; shared KV/cache reuse is prohibited unless
  safety is proven.
- Priority distinguishes interactive, urgent operational, background, and
  fairness work. Grace’s first-tenant status must not starve other residents.
- Queueing is priority-aware with fairness/aging; queue wait is observable.
- Admission control enforces active-generation, context-memory, and VRAM
  limits. Concurrency is resource-policy-driven.
- Residency records loaded model, footprint, warm/cold state, load/eviction,
  and measured GPU memory; configuration alone is not residency evidence.
- Contention records queue, admission, load, generation, end-to-end latency,
  utilization, evictions, and starvation.
- Simultaneous Grace/other-resident requests are admitted, queued, shed, or
  escalated by policy with independent leases and results.
- Cancellation, deadlines, orphan recovery, and idempotent result handling are
  mandatory; stale work cannot write another resident’s result.
- Diagnostics expose resident, tier, implementation, provider, resource,
  capacity snapshot, state, and failure reason.

Exact SLOs, weights, fairness, preemption, and whether home cognition keeps a
reserved slice are open Steward decisions. This section specifies extension
points, not implementation.

## 9. Provenance and truthfulness

Every cognition, transition, recommendation, handoff, execution, validation,
and acceptance record carries:

event_id, event_type, actor_class, actor_id, resident_id, occupant_id,
office_id, cognition_tier, implementation_id, provider_id, model_ref,
resource_id, request_id, correlation_id, causation_id, packet_id,
authoritative_state_refs, evidence_refs, policy_version, classification,
live_generation, timestamp, status, predecessor/supersession, and
validation_refs.

Canonical actor classes are:
deterministic_substrate, grace_home_cognition, grace_high_reasoning,
external_reasoning, codex_worker_execution, engineering_validation, and
steward_decision.

live_generation=false is mandatory for deterministic events. Grace events
require live_generation=true and actual implementation/provider/resource
identity. External, worker, validation, and Steward events retain their own
classes. “Grace decided” is legal only when a correlated Grace cognition event
with a recommendation/decision exists; otherwise use “the scheduler
transitioned,” “the worker reported,” “validation found,” or “the provider
advised.”

The existing [Artifact Provenance Model](docs/operations/Artifact_Provenance_Model_v1.md)
remains useful for artifacts, but it cannot replace this event-level envelope.

## 10. Failure and recovery rules

All failures fail closed, preserve request/packet/evidence lineage, and expose
the next action.

| Failure | Required behavior |
|---|---|
| Home unavailable | Continue only safe deterministic work; hold/shed/escalate cognition truthfully; never fabricate Grace output |
| High busy | Hold with capacity/ETA evidence or use approved external advice; do not consume high capacity for pointless escalation |
| High timeout | Verify lease/process/resource/partial output, record timeout, release capacity, and retry only under idempotent/new-attempt rules |
| External unavailable | Record unavailable/attempted truth; use eligible local high or Steward escalation; never invent result |
| Malformed result | Reject schema/correlation/classification failure; preserve bounded evidence; do not execute |
| Uncertain result | Return uncertainty explicitly and require home/high/Steward follow-up as consequence dictates |
| Tier disagreement | Preserve both results; high may adjudicate only under policy; material unresolved disagreement goes to Steward |
| Capacity exhausted | Use held_for_capacity/saturated, priority and fairness; never relax authority/classification constraints |
| Stale packet/evidence | Reassemble from authoritative state and create a new attempt/correlation |
| Identity/binding mismatch | Stop and reject; no result crosses resident or implementation boundary |

## 11. Future acceptance-test matrix

These are requirements, not claims that the current runtime passes them.

| ID | Scenario | Required proof |
|---|---|---|
| A1 | Routine decision | Home live-generation event; no high request |
| A2 | Difficult decision | Home escalation reason, bounded packet, typed high result, home continuation |
| A3 | Pointless escalation | Routine request leaves 4090/high counters unchanged |
| A4 | Consequential ambiguity | Deterministic path refuses; cognition or Steward escalation recorded |
| A5 | Return path | Recommendation, rationale, uncertainty, constraints, unresolved questions, next-tier flag and correlation |
| A6 | External boundary | External advisory provenance; no direct execution/acceptance |
| A7 | Other resident addressability | Another resident remains isolated and addressable during Grace work |
| A8 | Shared contention | Priority, queue, capacity, wait, release, fairness, and no identity collision |
| A9 | Replacement | Model/provider replacement preserves occupant/office/state and predecessor history |
| A10 | Provenance | Actual tier/provider/model/resource identified for every cognition event |
| A11 | No masquerade | Polling/leases/retries/bookkeeping cannot render as Grace reasoning |
| A12 | Home failure | Safe substrate continues; cognition holds/escalates truthfully |
| A13 | High busy/timeout | Packet lineage, leases, retries, and logical idempotency are preserved |
| A14 | Malformed/disagreement | Fail closed; no execution; correct re-escalation |
| A15 | Packet minimization | Only required context crosses tier/provider boundary |

## 12. Existing seams to reuse

1. ResidentImplementationRuntime, ImplementationBinding, and transition
   runtime for identity-preserving implementation replacement.
2. ResidentContextAssembler, ContextBundle, policy decisions, dependency
   fingerprints, and renderer for bounded packets.
3. Provider-neutral reasoning contracts, registry, and local adapters.
4. CognitiveEscalationRuntime for advisory correlation/classification.
5. RiverEvent/EventStore and operational event records for lineage.
6. GraceConsultationLoop for bounded consultations, capacity holds,
   continuations, transport recovery, and truthful unavailable outcomes.
7. Provider health/capacity, routing recommendations, governed reservation,
   dispatch, and execution adapters.
8. Existing Grace response/provenance guards and focused resident/CME tests.

Reuse must be through bounded adapters. Existing names are not compliance
evidence without behavior verification.

## 13. Explicit non-goals

- No runtime implementation, routing change, migration, model assignment, or
  current Grace behavior change.
- No final 8B or 3032B model selection and no hardcoded GPU-to-Grace mapping.
- No universal resident cognition, tool, memory, authority, or queue policy.
- No silent provider/tier fallback, transcript replay as identity, external
  authority, direct execution, acceptance, merge, or protected-data bypass.
- No replacement of CME, Dispatch, provider governance, or Steward authority.
- No attempt to solve all future residents, security, or sensitive-domain policy.

## 14. Open questions requiring Steward decision

1. Initial home/high interactive and background latency SLOs and home-failure
   threshold.
2. Consequence/risk classes that mandate high reasoning.
3. Whether “3032B-class” is a benchmark, preferred deployment class, or gate.
4. Approved external providers, classifications, retention, and locality.
5. Initial 3060 sharing policy: reservation, weighted fairness, time slicing,
   or another policy.
6. Whether high reasoning may preempt/evict home cognition.
7. Which recommendations may exercise delegated authority versus always require
   a separate execution/acceptance actor.
8. Disagreement threshold requiring immediate Steward review.
9. Packet/output retention and redaction policy for protected local content.
10. First accepted Grace tenant bindings after this specification is approved.

## 15. Conclusion

The repository already contains strong identity, context, provider-neutral,
advisory-escalation, CME, capacity, and provenance seams. It does not yet
prove the multi-tier behavior in this contract, especially home-vs-high
selection, shared 3060 resident fairness, or mandatory cognition-event
provenance. That distinction is part of GRC-002: designed, implemented,
tested, live-accepted, and running remain separate claims.
