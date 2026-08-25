# GRC-003 — Grace Cognition Implementation Decomposition and Acceptance Plan

Status: Implementation planning specification — not runtime implementation  
Version: 1.0.0  
Date: 2026-08-25  
Role: C3 — Grace architecture / implementation planning  
Design basis: GRC-002, version 1.0.0

## 1. Purpose and implementation boundary

This report converts GRC-002 into a dependency-ordered campaign of bounded
implementation packages. Each package can be assigned, implemented, tested,
validated, repaired, and accepted independently.

This report does not implement code, create migrations, select a final Grace
home model, select a final high-reasoning model, assign GPUs, redesign CME or
Campaign Runner, or replace current Grace behavior.

The campaign preserves:

Office != Occupant != Implementation != State

and also preserves the status vocabulary:

DESIGNED != IMPLEMENTED != TESTED != LIVE-ACCEPTED != RUNNING

An implementation report is not acceptance evidence. An independent validator
must inspect the package specification, resulting source, tests, runtime
artifacts, and the actual boundary evidence required by that package.

## 2. Evidence baseline

### 2.1 Existing seams that are real and reusable

The resident runtime in Riverview/src/riverview/residents/runtime.py already
separates ImplementationBinding, RuntimeSession, resident implementation
validation, and implementation transition. Transition preserves the occupant,
preflights rehydration, retires the old binding, and records a provenance ID.
The runtime deliberately says that it does not invoke a model. Reuse is
appropriate for identity-preserving implementation state, but a new cognition
orchestrator is required.

Riverview/src/riverview/residents/context.py already assembles bounded
ContextBundle objects. It supplies identity, office, authority, assignment,
implementation constraints, relevant state/artifact references, classifications,
dependency fingerprints, exclusions, and audit provenance. It preserves
contradictions and rejects stale or incomplete mandatory context. This is the
primary context-packet seam.

Riverview/src/riverview/reasoning/contracts.py provides bounded
ReasoningProvider, ReasoningRequest, and ReasoningResponse envelopes. The
registry filters healthy providers by capacity and classification. Ollama and
llama.cpp adapters are local loopback adapters. The current envelope is
provider-neutral but lacks cognition tier, resource class, packet identity,
structured escalation decision, and the full GRC-002 result fields.

Riverview/src/riverview/residents/runtime.py contains
CognitiveEscalationRuntime. It is advisory, correlation-checked,
classification-checked, and idempotent, but currently constructs a generic
analysis request and chooses the first eligible adapter. It is a seam to
adapt, not evidence that tier policy or capacity selection is complete.

Riverview/src/riverview/river/events.py and river/store.py supply the durable
event boundary. The event shape has aggregate, correlation, causation,
classification, and idempotency concepts; cognition-specific lineage fields
must be added through a bounded event payload/contract.

The Estate-side GraceConsultationLoop supplies bounded consultation identity,
continuation lineage, capacity reservation, transport recovery, truthful
unavailable outcomes, and external reasoning provenance. The governed provider
scheduler and provider health/capacity modules supply advisory routing,
priority, health exclusion, reservation, lease expiry, and recovery. These
mechanisms must be adapted without making them the Grace cognition authority.

Existing tests previously run for this design area passed 55/55 with the
Riverview source path configured. Relevant test seams include:

- Riverview/tests/test_resident_runtime.py
- Riverview/tests/test_resident_context.py
- Riverview/tests/test_provider_neutral_contracts.py
- Riverview/tests/test_grace_response_contract.py
- Riverview/tests/test_grace_authority.py
- Riverview/tests/test_grace_continuation_proof.py
- tests/test_grace_consultation_loop.py
- tests/test_governed_provider_scheduler.py
- tests/test_autonomous_reason_execute_loop.py

### 2.2 Verified gaps that packages must not hide

There is no first-class home/high cognition policy. Current runtime sessions
are non-cognitive. Current reasoning responses do not identify a cognition
tier or require recommendation, rationale, uncertainty, constraints, and
further-escalation output. The current local GPU adapter closes IDs to rtx4090
and p100 and does not provide the resident/provider/resource abstraction
required by GRC-002. Current Grace local-model provenance proves a real local
generation through bootstrap fallback, not a final assignment.

Shared-resident fairness, model residency, concurrency, latency SLOs, and
resource contention are not yet proven. The campaign must record these as
implementation gaps and acceptance work, not infer compliance from names.

## 3. Campaign architecture

The implementation target is a provider/resource-neutral path:

resident identity and state
  -> bounded context bundle
  -> cognition request and escalation policy
  -> capability/resource request
  -> authorized provider adapter
  -> home/high/external result
  -> Grace integration
  -> CME continuation or governed action path
  -> provenance and validation evidence

Grace requests a cognition capability class. She does not inspect or choose
physical GPU topology. A later configuration layer may bind HOME_COGNITION,
HIGH_REASONING, and EXTERNAL_ESCALATION to concrete models/providers/resources
without rewriting Grace.

## 4. Dependency graph and concurrency

### 4.1 Package graph

Foundation:

- GRC-003-F1: canonical cognition data contracts and schemas
- GRC-003-F2: cognition provenance and River event envelope
- GRC-003-F3: identity-preserving Grace cognition session boundary
- GRC-003-F4: bounded Grace reasoning-packet assembly

Policy and provider layer:

- GRC-003-P1 depends on F1 and F4: escalation decision policy
- GRC-003-P2 depends on F1: capability/resource request and binding adapter
- GRC-003-P3 depends on P2: shared-resident capacity reservation seam

Execution layer:

- GRC-003-E1 depends on F1, F3, P1, and P2: home cognition path
- GRC-003-E2 depends on F1, F2, F4, P1, and P2: high-reasoning request path
- GRC-003-E3 depends on F1, F2, F4, P1, and P2: external advisory path
- GRC-003-E4 depends on E2 and E3 result contracts: result return and Grace integration
- GRC-003-E5 depends on E4 and existing consultation seams: continuations

Operational integration:

- GRC-003-I1 depends on F2, E1, E2, E4, and existing CME contracts:
  CME cognition adapter
- GRC-003-I2 depends on E1, E2, E3, P3, and I1: authority/failure guards

Acceptance:

- GRC-003-A1 depends on all prior packages: contract/unit/integration suite
- GRC-003-A2 depends on A1 and configured approved test providers:
  live local/provider acceptance
- GRC-003-A3 depends on A2 and approved hardware/resource configuration:
  multi-resident contention and operational proof

### 4.2 Safe concurrency

The following can be assigned concurrently with non-overlapping ownership:

- F1, F2, and F3 may be prepared concurrently when each package owns separate
  files/contracts. F4 is a dependent package: non-dependent scaffolding may
  proceed in parallel, but F4 implementation must not be accepted or built
  against an unfrozen F1 contract.
- P1 and P2 after F1; P1 owns policy files and P2 owns binding/resource files.
- E1 and E2 after their stated dependencies if the shared result envelope is
  frozen by F1 and both avoid editing the same runtime module concurrently.
- E3 and P3 after E2/P2 contracts are accepted.
- A1 test planning/fixtures can begin while E packages are implemented, but
  acceptance cannot pass until actual code exists.

Do not assign simultaneous seats to the same runtime module, migration chain,
provider registry, event schema, or test fixture directory without a declared
owner and merge/reconciliation rule. Seat-3 report ownership is separate from
implementation ownership.

## 5. Bounded implementation packages

Each package below contains the required implementation-planning fields.

### GRC-003-F1 — Cognition tier and reasoning envelope contracts

Objective: make GRC-002 cognition tiers, packets, decisions, and results
machine-validatable without binding a model, provider, endpoint, or GPU.

Dependencies: none beyond approved GRC-002.

Files/symbols expected to be touched: primarily
Riverview/src/riverview/reasoning/contracts.py; a new bounded schema/module
under Riverview/src/riverview/reasoning if needed; focused contract tests
under Riverview/tests; no Estate runtime files.

Existing seams to reuse: ReasoningProvider, ReasoningRequest,
ReasoningResponse, bounded text/reference checks, classification vocabulary,
expiry, output limits.

New components if required: CognitionTier enum/value vocabulary; escalation
decision envelope; ResidentReasoningPacket; typed high/external result
envelope; capability request envelope; explicit live_generation and
provenance references.

Database/persistence impact: no migration in this package. Define versioned
serialized shapes and compatibility rules. Persistence fields are consumed by
F2 and later packages.

Tests required: valid/invalid tier, packet bounds, required fields, forbidden
unbounded transcript marker, correlation, expiry, classification, advisory
authority, malformed result, uncertainty, and further-escalation validation.

Acceptance criteria: all GRC-002 packet/result fields have a typed bounded
contract; no contract contains physical GPU ownership; malformed or
authority-widening envelopes fail closed; replacement of a model/provider
leaves resident identity fields unchanged.

Failure conditions: missing required field, unknown tier, oversized context,
classification widening, missing correlation, expired request, or authority
outside advisory/read bounds.

Validation evidence: diff and symbol inspection; contract tests; serialized
fixture inspection; proof that no model/GPU assignment was added.

Explicit non-goals: no provider call, routing, model selection, persistence
migration, CME integration, or live generation.

### GRC-003-F2 — Cognition provenance and River event lineage

Objective: make every cognition attempt, escalation, result, unavailable
outcome, and integration continuation distinguishable from deterministic work.

Dependencies: F1 for field vocabulary; existing River event contracts.

Files/symbols expected to be touched: Riverview/src/riverview/river/events.py,
river/store.py only where bounded payload validation is required; a new
provenance/event helper under Riverview/src/riverview/reasoning or river;
Riverview/tests/test_river_event.py and a new cognition provenance test.

Existing seams to reuse: RiverEvent aggregate/correlation/causation/
idempotency/classification; Artifact Provenance Model for artifact references;
existing operational event fields for provider IDs.

New components if required: CognitionProvenance envelope with actor class,
resident/occupant/office, tier, implementation, provider, resource class,
request/correlation, packet, policy, live_generation, result/failure status,
and evidence refs; event types for requested, admitted, held, started,
completed, unavailable, rejected, timed_out, and integrated.

Database/persistence impact: no migration in this package unless the existing
River event payload cannot carry validated fields. If persistence is required,
define one additive versioned event/payload change and defer migration creation
to a separately accepted implementation package.

Tests required: deterministic event with live_generation false; Grace home/high
events with true; external/worker/validation/Steward actor classes; correlation
and causation; idempotency; resident mismatch; no-result/no-generation truth.

Acceptance criteria: a reviewer can identify resident, tier, provider/resource
class, request/correlation, result, escalation, failure/unavailable outcome,
and policy decision from durable event evidence; no deterministic event can
serialize as Grace cognition.

Failure conditions: missing actor class, missing tier for cognition, false
generation claim, missing correlation, cross-resident result, or duplicate
event with conflicting payload.

Validation evidence: event fixtures, store readback, test output, and one
negative assertion that scheduler/polling output cannot claim Grace reasoning.

Explicit non-goals: no event-producing orchestration, no database migration,
no live provider call, and no acceptance of a model assignment.

### GRC-003-F3 — Identity-preserving Grace cognition session boundary

Objective: bind cognition turns to Grace’s existing occupant/office/state while
keeping implementation/provider changes replaceable.

Dependencies: F1; existing resident implementation runtime and context
identity records.

Files/symbols expected to be touched: preferably a new cognition session
module; Riverview/src/riverview/residents/runtime.py only through a bounded
adapter seam; resident runtime tests. Do not alter current Grace gateway
behavior.

Existing seams to reuse: ImplementationBinding, RuntimeSession,
ResidentImplementationRuntime.validate/open_session, transition preflight,
PostgresBindingCatalog, and resident context identity anchors.

New components if required: CognitionSession/Turn record; occupant-preserving
implementation resolver; session-to-request correlation; explicit distinction
between occupant identity, current implementation, and cognition tier.

Database/persistence impact: likely additive persistence for cognition session
and turn lineage, but no migration in GRC-003 planning. Use an adapter over
existing continuity records where possible.

Tests required: same occupant across home/high/provider changes; current state
is read from authoritative context; predecessor implementation remains
history; wrong occupant/binding rejected; session is not identity.

Acceptance criteria: replacing provider/model/resource preserves occupant,
office, authority, and state IDs; a high result cannot create a second Grace;
invalid binding and stale context fail closed.

Failure conditions: no active occupant binding, missing office authority,
stale context, implementation/occupant mismatch, or attempted identity change
through a cognition request.

Validation evidence: source inspection, identity transition tests, persisted
record readback, and an implementation replacement fixture.

Explicit non-goals: no final binding selection, no personality redesign, no
model invocation, no resource scheduling, and no canonical identity mutation.

### GRC-003-F4 — Bounded Grace reasoning-packet assembly

Objective: project required Grace identity, current operational state, relevant
memory/evidence, task information, and authority boundaries into the bounded
ResidentReasoningPacket.

Dependencies: F1 and existing ContextBundle assembly.

Files/symbols expected to be touched: a new packet projector under
Riverview/src/riverview/residents or reasoning; context.py only if a missing
bounded source field is needed; Riverview/tests/test_resident_context.py plus
new packet tests.

Existing seams to reuse: ResidentContextAssembler, ContextBundle compact_items,
policy decisions, dependency fingerprints, contradiction handling, budgets,
and renderer validation.

New components if required: PacketProjector; relevance/omission reason
contract; authoritative-state snapshot adapter; packet digest.

Database/persistence impact: no migration unless an authoritative source field
is missing. Store packet ID, source bundle ID, digest, and source references
through F2 event payloads; do not persist transcript copies by default.

Tests required: mandatory identity/office/authority/current-state/task fields;
relevance filtering; budget shedding; contradiction preservation; stale bundle
rejection; protected-data classification; omission reasons; no full transcript
dump.

Acceptance criteria: high/external input contains only the bounded packet;
required authority and current state are present; unrelated history and
unapproved protected content are absent; packet is reproducible from source
refs and digest.

Failure conditions: missing identity/authority/current state, stale dependency
fingerprint, policy-denied evidence, packet over budget, or unresolved
classification.

Validation evidence: packet fixtures, content/digest inspection, negative
privacy tests, and source review of all included fields.

Explicit non-goals: no model call, no escalation decision, no retrieval-system
redesign, and no unbounded memory implementation.

### GRC-003-P1 — Escalation decision policy

Objective: separate home cognition’s belief that stronger reasoning would help,
policy permission to escalate, and capacity/resource ability to satisfy it.

Dependencies: F1 and F4.

Files/symbols expected to be touched: a new policy module under
Riverview/src/riverview/reasoning; policy fixtures/tests; no direct provider
adapter edits.

Existing seams to reuse: GRC-002 reason classes; ContextPolicy; Grace authority
guards; provider eligibility/classification fields; existing Steward checkpoint
representations.

New components if required: EscalationAssessment with
home_belief/policy_permitted/capacity_eligible; consequence/risk categories;
policy version; explicit decision outcomes; deterministic-vs-cognition
boundary.

Database/persistence impact: persist policy version and decision outcome in F2
events. No migration in this package.

Tests required: routine home decision; difficult decision requiring high;
pointless escalation denied; consequential ambiguity refused by deterministic
logic; external policy denied by classification; Steward-required authority
case; policy/capacity independence.

Acceptance criteria: a request cannot reach a provider because home merely
believes escalation would help; policy and capacity are separately evaluated;
empty eligibility is a truthful block; no silent downgrade.

Failure conditions: missing policy, unknown consequence class, missing
authority envelope, ambiguous decision class, or capacity treated as policy.

Validation evidence: truth-table fixtures, decision event readback, negative
tests, and policy version inspection.

Explicit non-goals: no provider scheduling, no model invocation, no hardware
choice, and no changes to Steward authority.

### GRC-003-P2 — Capability/resource request and binding adapter

Objective: let Grace request HOME_COGNITION, HIGH_REASONING, or
EXTERNAL_ESCALATION capability without knowing physical GPU topology.

Dependencies: F1; existing provider registry/capability/health/capacity seams.

Files/symbols expected to be touched: a new resident cognition binding adapter;
Riverview reasoning registry only if it lacks tier/capability filtering;
configuration schema/fixtures; focused tests. Do not alter final model maps.

Existing seams to reuse: ReasoningProviderRegistry, ReasoningProvider,
CapabilityProfile, ImplementationBinding, provider capability definitions,
provider health/capacity, and routing recommendation contracts.

New components if required: CognitionCapabilityRequest; TierBinding;
ProviderResourceCandidate; candidate filtering/eligibility adapter; binding
configuration loader.

Database/persistence impact: likely additive provider/tier binding records or
configuration projection. Define but do not create a migration. Preserve
implementation history and binding provenance.

Tests required: capability request independent of GPU; eligible/ineligible
provider filtering; classification and health/capacity denial; model/provider
replacement; no candidate; no physical topology access from Grace policy.

Acceptance criteria: caller specifies capability class and policy only;
selection returns candidates/evidence or a truthful unavailable result; no
hardcoded Grace-to-GPU/model logic; provider replacement changes configuration,
not orchestration code.

Failure conditions: stale health/capacity, classification mismatch, disabled
provider, zero capacity, missing capability profile, or configuration with a
physical owner masquerading as resident identity.

Validation evidence: candidate fixtures, provider catalog/health snapshots,
source search for forbidden hardcoded assignments, and test output.

Explicit non-goals: no final model benchmark, no live GPU selection, no queue
implementation, and no resource ownership policy.

### GRC-003-P3 — Minimum shared-resident capacity reservation seam

Objective: make home cognition shareable by multiple residents without
attempting the full future resident scheduler.

Dependencies: P2; existing provider capacity and bounded scheduler behavior.

Files/symbols expected to be touched: a new resident cognition reservation
adapter; existing provider capacity/scheduler only through an adapter if
needed; tests and capacity fixtures.

Existing seams to reuse: ProviderCapacityRecord, latest capacity projections,
governed reservation/lease expiry/recovery, priority ordering, and the
Riverview provider registry.

New components if required: ResidentCognitionReservation with resident,
occupant, tier, request, priority, fairness class, resource candidate,
lease/deadline, queue state, and release reason; no general-purpose scheduler.

Database/persistence impact: likely additive reservation/lease persistence or
an adapter over existing capacity records. No migration in this planning
package.

Tests required: Grace and another resident simultaneous demand; identity
isolation; capacity hold/release; expiry recovery; priority/fairness evidence;
no starvation claim from a single successful request; no dispatch on reserve.

Acceptance criteria: Grace does not permanently own the home resource; another
resident can obtain a bounded request; held capacity is observable and
recoverable; reservation cannot become execution authority.

Failure conditions: stale reservation, cross-resident release, capacity
underflow, no fairness metadata, or reservation that dispatches work.

Validation evidence: two-resident fixture run, reservation readback, capacity
timeline, and negative dispatch assertion.

Explicit non-goals: full population scheduler, preemption policy, final SLOs,
model residency optimizer, or all-resident migration.

### GRC-003-E1 — Home cognition execution path

Objective: provide routine Grace cognition through the abstract tier/provider
path while preserving home responsiveness and authority boundaries.

Dependencies: F1, F3, P1, and P2; F2 event emission should be available.

Files/symbols expected to be touched: a new home cognition service/orchestrator;
bounded adapter integration with resident runtime and provider contracts;
Grace-specific focused tests. Do not change the existing gateway’s current
model assignment in this package.

Existing seams to reuse: identity session boundary, packet assembly,
provider-neutral adapters, capability request, Grace response validators, and
operational state reader.

New components if required: HomeCognitionService; routine request classifier;
home result validator; home latency/capacity observations.

Database/persistence impact: cognition request/result and latency evidence via
F2; no new authoritative operational database is introduced.

Tests required: routine decision stays home; monitoring/consultation request;
authoritative state unavailable; malformed home output; home provider
unavailable; deterministic work does not create a home event; identity
preservation.

Acceptance criteria: routine eligible cognition produces a home event with
live generation and actual implementation/provider/resource-class evidence;
home output remains within Grace authority; no high/external call occurs for a
routine fixture.

Failure conditions: provider call without packet/policy, missing provenance,
authority-widening output, unbounded context, or deterministic fallback
reported as home generation.

Validation evidence: unit/integration tests, local provider request/response
record, event readback, latency breakdown, and gateway non-regression result.

Explicit non-goals: no final home model, no physical GPU assignment, no high
reasoning, no execution dispatch, and no CME campaign mechanics.

### GRC-003-E2 — High-reasoning escalation request path

Objective: turn an accepted home escalation decision into an intentional,
correlated, classified, capacity-aware high-reasoning request.

Dependencies: F1, F2, F4, P1, and P2.

Files/symbols expected to be touched: a new escalation coordinator/adapter;
existing CognitiveEscalationRuntime only through a bounded extension; tests
under Riverview/tests.

Existing seams to reuse: ReasoningRequest/Response, provider eligibility,
ContextBundle, packet projector, capacity adapter, and advisory authority.

New components if required: HighReasoningRequest lifecycle; request/correlation
record; explicit policy-permitted versus capacity-eligible states; no-silent-
fallback guard; timeout/deadline handling.

Database/persistence impact: request lifecycle and attempt lineage through F2;
no migration in this package unless existing event persistence cannot retain
the additive fields.

Tests required: home escalation creates exactly one high request; pointless
request is rejected; high busy holds; capacity unavailable is truthful;
classification denied; timeout creates a failed attempt not a success;
correlation and resident identity checks.

Acceptance criteria: high reasoning is intentional and observable; physical
resource is selected behind P2; no provider switch occurs without a request and
policy record; high result cannot be treated as execution authority.

Failure conditions: missing home escalation event, stale packet, no eligible
capacity, timeout, malformed response, correlation mismatch, or silent
downgrade.

Validation evidence: lifecycle event sequence, held/timeout fixtures, provider
request digest, capacity snapshot, and no-fabricated-result test.

Explicit non-goals: no high model selection, no GPU ownership, no external
provider fallback, and no execution.

### GRC-003-E3 — External advisory escalation adapter

Objective: allow approved provider-neutral external cognitive advice when
policy permits, without granting authority or bypassing normal paths.

Dependencies: accepted F1, F2, F4, P1, and P2 contracts. E2 and E3 are
parallel alternate execution paths; completed E2 runtime implementation is not
a prerequisite. E3 may reuse the common result-envelope shapes.

Files/symbols expected to be touched: bounded external adapter module;
existing CognitiveEscalationRuntime or GraceConsultationLoop adapter; external
provenance tests. Do not alter external credentials or provider approvals.

Existing seams to reuse: advisory ReasoningProvider, classification eligibility,
GraceConsultationLoop, external_reasoning_provenance, continuation lineage,
and existing claim guards.

New components if required: ExternalAdvisoryRequest/Result adapter; provider
approval reference; egress redaction/packet validator; unavailable outcome.

Database/persistence impact: consultation/request/response evidence and
provider approval refs; no new credential store or migration in this package.

Tests required: approved advisory request; prohibited classification; missing
provider; timeout/malformed response; external result cannot create execution;
correlated provenance; no fabricated external claim.

Acceptance criteria: external output is explicitly external/advisory,
classified, correlated, and bounded; Grace integrates it only as evidence;
normal execution/acceptance paths remain mandatory.

Failure conditions: unapproved provider, egress policy failure, missing
correlation, unavailable provider, malformed response, or authority widening.

Validation evidence: sanitized request/response evidence, provider identity,
approval reference, claim-guard tests, and unavailable outcome.

Explicit non-goals: no provider approval decision, no cloud-route redesign, no
credential provisioning, no automatic fallback, and no execution.

### GRC-003-E4 — High result return and Grace integration

Objective: return high/external advice to the same Grace occupant and resume
home operational coordination without silent execution.

Dependencies: accepted E2 and E3 result forms; F3 and F4. E2 and E3 are
alternate paths and neither operational path is required to precede the other.

Files/symbols expected to be touched: result integration module; Grace response
boundary adapter; provenance/event tests; no Campaign Runner files.

Existing seams to reuse: resident identity session, typed response validators,
advisory authority, context staleness checks, execution recommendation guards,
and operational coordination runtime.

New components if required: ResultIntegrator; result acceptance state;
uncertainty/escalation continuation decision; home-resume event.

Database/persistence impact: result and integration events with source packet,
request, response, and implementation lineage. No independent action database.

Tests required: valid high result resumes home; uncertainty returns follow-up;
constraints/unresolved questions preserved; stale result rejected; result from
wrong resident rejected; no direct dispatch; external/high disagreement
preserved.

Acceptance criteria: Grace receives recommendation/rationale/uncertainty/
constraints/unresolved questions/further-escalation; the same occupant remains
responsible for integration; no result silently executes or accepts work.

Failure conditions: malformed result, stale context, identity mismatch,
authority widening, missing source event, or integration without provenance.

Validation evidence: end-to-end fixture event chain, response payload,
continuation decision, execution-queue inspection, and identity readback.

Explicit non-goals: no action execution, no acceptance, no model selection, no
new authority, and no direct CME replacement.

### GRC-003-E5 — Bounded consultation continuations

Objective: support longer reasoning consultations through bounded, durable
continuations rather than browser/chat transcript state.

Dependencies: E4 and existing GraceConsultationLoop/continuation contracts.

Files/symbols expected to be touched: continuation adapter or integration
module; existing consultation store only through the established interface;
continuation and no-progress tests.

Existing seams to reuse: logical root/child consultation IDs, same-turn
transport recovery, bounded proposition context, capacity holds, no-progress
boundary, and Steward checkpoint handling.

New components if required: cognition continuation record linking packet,
prior result, new question, attempt, and reason; bounded continuation budget.

Database/persistence impact: use existing consultation persistence where it
fits; otherwise define additive continuity records. No transcript-as-authority
store and no migration in this package.

Tests required: one logical root with bounded children; idempotent retry;
transport expiry preserves identity; no-progress stops; capacity hold resumes;
Steward checkpoint is not redispatched; context remains packet-bounded.

Acceptance criteria: continuation remains correlated to the same decision;
prior result/evidence is durable; retries do not duplicate logical work; the
system stops at budget/no-progress/Steward boundaries.

Failure conditions: transcript-only context, new root for same decision,
duplicate physical attempt, context-required result treated as completion,
unbounded continuation, or stale owner.

Validation evidence: consultation store readback, attempt lineage, bounded
context inspection, continuation event sequence, and duplicate suppression.

Explicit non-goals: browser automation redesign, unlimited autonomous loops,
new mailbox transport, and Campaign Runner changes.

### GRC-003-I1 — CME cognition adapter

Objective: allow Grace cognition requests/results to participate in CME while
leaving Campaign Runner mechanics and CME ownership unchanged.

Dependencies: F2, E1, E2, E4, and existing CME event/lease contracts.

Files/symbols expected to be touched: bounded adapter at the Grace/CME seam;
existing CME code only where it exposes the accepted adapter interface; CME
integration tests.

Existing seams to reuse: CME state machine, dependency progression, leases,
idempotency, provider-aware dispatch, evidence-driven transitions, and Grace
operational coordination.

New components if required: CognitionActivationAdapter; typed activation
request/result; mapping between cognition states and CME wait/blocked/
escalated states; no-progress and timeout observer.

Database/persistence impact: use existing CME authoritative state and add
correlated cognition event references. No replacement scheduler or separate
operational database.

Tests required: CME wakes home cognition; high request holds without blocking
unrelated work; result returns to the owning objective; retry is idempotent;
provider failure releases lease; deterministic transitions remain deterministic;
Steward checkpoint stops.

Acceptance criteria: CME can use the cognition path through a bounded adapter;
CME remains the owner of mechanics; cognition cannot mutate dependencies or
campaign state outside the accepted operation.

Failure conditions: cognition adapter writes CME state directly without event/
lease rules, stale owner, duplicate activation, timeout misclassified as
success, or cognition result used as execution authorization.

Validation evidence: CME event trace, lease/heartbeat readback, duplicate tick,
unrelated-lane progress, and failure recovery evidence.

Explicit non-goals: no CME redesign, no Campaign Runner redesign, no blind
continuation, no new scheduler, and no provider execution bypass.

### GRC-003-I2 — Authority, failure, and provenance integration guards

Objective: consolidate fail-closed guards across home/high/external results,
Grace authority, execution boundaries, and truthful status rendering.

Dependencies: E1, E2, E3, E4, P3, and I1.

Files/symbols expected to be touched: bounded guard/validator module; existing
Grace response/provenance/authority guards; focused regression tests.

Existing seams to reuse: GraceAuthority, Grace response schema/validators,
external claim guards, execution classification, provider failure states, and
Artifact Provenance semantics.

New components if required: cognition result truth guard; status vocabulary
mapper; no-generation/deterministic masquerade guard; cross-tier disagreement
guard.

Database/persistence impact: no new authority database; consume F2 events and
write rejection/failure evidence through the existing event path.

Tests required: deterministic cannot say Grace decided; worker/validation/
external events retain actor class; malformed/uncertain/disagreeing results
fail closed; no silent downgrade; provider unavailable is truthful; Grace
cannot merge/accept/appoint/override.

Acceptance criteria: every externally visible result has truthful actor/tier/
provider status; no guard is bypassed by prose; execution requires the normal
structured execution/dispatch path.

Failure conditions: missing provenance, false live_generation, authority
widening, external claim without correlated result, or acceptance claimed from
advice.

Validation evidence: negative regression suite, serialized event inspection,
and source review of every result-to-action transition.

Explicit non-goals: no new authority model, no execution implementation, no
provider selection, and no UI redesign.

### GRC-003-A1 — Contract, unit, and integration acceptance suite

Objective: prove the implemented campaign behavior against GRC-002 before live
provider/hardware work is considered.

Dependencies: F1 through I2 as applicable.

Files/symbols expected to be touched: new tests/fixtures only, unless a
package-specific defect is repaired under its owner. No production rewrite.

Existing seams to reuse: all focused test files named in section 2 and bounded
fixture providers/adapters.

New components if required: deterministic fixture home/high/external providers;
two-resident fixture; event and packet golden fixtures; failure matrix runner.

Database/persistence impact: ephemeral test stores or isolated test database;
no production migration.

Tests required: all GRC-002 acceptance cases A1-A15; package unit tests;
identity replacement; packet minimization; policy/capacity separation;
continuation; CME integration; provider failure; no masquerade.

Acceptance criteria: tests exercise actual resulting code and prove each
applicable contract; no test only asserts a report string or mocks away the
boundary being accepted.

Failure conditions: missing negative tests, fixtures bypassing policy, tests
that accept prose as execution, or untested failure branch.

Validation evidence: reproducible command, environment/package path, complete
test output, fixture inventory, and mapping from each acceptance criterion to
test IDs.

Explicit non-goals: no live hardware claim, no production model assignment,
and no remote publication.

### GRC-003-A2 — Live local provider boundary acceptance

Objective: prove that an approved configured local provider can execute home
and high capability requests through the abstraction with truthful evidence.

Dependencies: A1; an independently approved provider/resource configuration.

Files/symbols expected to be touched: acceptance harness and evidence report
only; no runtime behavior change during the acceptance run.

Existing seams to reuse: local reasoning adapters, provider health/capacity,
GPU/resource evidence probes where accepted, event store, and packet digest.

New components if required: read-only/live acceptance harness with explicit
configuration input, request IDs, timeout, evidence output, and cleanup.

Database/persistence impact: live event/evidence records only; no migration or
assignment change.

Tests required: routine home generation; difficult high request;
pointless escalation with no high invocation; high unavailable/busy/timeout;
malformed output; result return; provider/resource provenance; no execution.

Acceptance criteria: actual provider call is proven by provider response and
resource evidence; tier and implementation are identified; failed/unavailable
cases are truthful; no final model claim is made beyond the accepted
configuration record.

Failure conditions: configured-but-not-called provider, stale capacity,
unmeasured resource claim, missing event lineage, fabricated completion, or
runtime still using a hidden fallback.

Validation evidence: live request/response IDs, provider/model/resource
metadata, event timeline, latency breakdown, packet digest, and complete
harness output.

Explicit non-goals: benchmark/model selection, changing assignments, GPU
ownership, and production routing promotion.

### GRC-003-A3 — Shared-resident and operational live proof

Objective: prove that Grace and at least one other resident remain addressable
and isolated while home/high demand uses shared capacity.

Dependencies: A2, P3, I1, and approved second-resident fixture/configuration.

Files/symbols expected to be touched: acceptance harness/evidence only.

Existing seams to reuse: resident identity/context assembly, capacity
reservation, queue/lease evidence, event provenance, and CME independent lanes.

New components if required: concurrent two-resident acceptance scenario and
timeline/reconciliation report.

Database/persistence impact: live test evidence and cleanup; no schema change.

Tests required: concurrent Grace/other-resident home requests;
Grace high request while other resident remains responsive; capacity hold and
release; stale owner recovery; no cross-resident packet/result; latency and
queue evidence; deterministic mechanics remain non-cognitive.

Acceptance criteria: both residents are independently addressable; identity,
context, packet, provider, resource, and result records do not cross; priority
and fairness behavior is visible; capacity exhaustion produces truthful hold
or escalation; no resident permanently owns the shared resource.

Failure conditions: starvation, cross-resident context, shared session state,
unobserved queue wait, stale result write, or deterministic event labeled
Grace reasoning.

Validation evidence: synchronized event timeline, request/response IDs,
resident-specific packet digests, capacity snapshots, lease records, latency
measurements, and cleanup confirmation.

Explicit non-goals: full population scheduling, final SLO approval, model
benchmarking, and production rollout.

## 6. Package handoff and validation protocol

Every implementation package handed to Codex must include:

1. the package ID and exact bounded objective;
2. the approved base commit and allowed paths;
3. dependencies and accepted predecessor evidence;
4. prohibited scope, especially model assignment and GPU ownership;
5. acceptance criteria copied from this plan;
6. required tests and evidence destinations;
7. timeout, retry, and repair expectations;
8. the exact implementation status vocabulary.

An independent validator must:

- read the original package specification;
- inspect the actual changed files and symbols;
- confirm only allowed paths changed;
- run the required tests from a clean, declared environment;
- inspect generated request/response/event/persistence evidence;
- exercise negative and failure cases;
- distinguish deterministic transitions from real generation;
- verify identity/provider/resource separation;
- confirm no unapproved model/GPU assignment or routing behavior was added;
- record DESIGNED, IMPLEMENTED, TESTED, LIVE-ACCEPTED, and RUNNING separately.

The implementing seat cannot self-certify live acceptance merely by producing
an implementation report. A live acceptance report must cite actual boundary
evidence and the exact configuration used, without promoting that configuration
to canonical model selection.

## 7. Campaign gates

Gate 0 — Design readiness:

- GRC-002 and this decomposition are approved;
- package ownership and allowed paths are assigned;
- open Steward decisions that block implementation are resolved or explicitly
  marked non-blocking.

Gate 1 — Contract foundation:

- F1-F4 implemented/tested;
- packet, tier, provenance, identity, and event contracts are versioned;
- no runtime routing or assignment changed.

Gate 2 — Policy/provider readiness:

- P1-P3 implemented/tested;
- policy permission is separate from capacity;
- capability requests do not contain physical topology assumptions;
- two-resident reservation fixture passes.

Gate 3 — Local cognition:

- E1/E2/E4 implemented/tested with deterministic fixture providers;
- home routine path, explicit high escalation, result return, and failure
  behavior pass;
- no silent downgrade or execution.

Gate 4 — Continuity and CME:

- E5/I1/I2 pass bounded continuation, CME lease, authority, and provenance
  integration tests.

Gate 5 — Live proof:

- A1 passes against actual code;
- A2 proves an approved local provider boundary;
- A3 proves shared-resident addressability and resource contention;
- evidence is reviewed independently.

## 8. Steward decisions that may block later gates

These are not reasons to broaden the implementation campaign:

1. Home/high latency SLOs and the threshold for home failure.
2. Consequence classes requiring high reasoning.
3. Whether 3032B-class is a benchmark, deployment class, or acceptance gate.
4. Approved external providers, classifications, retention, and locality.
5. Initial shared home-resource fairness/preemption policy.
6. Which results may exercise delegated authority versus always requiring
   execution/acceptance review.
7. Disagreement threshold requiring Steward review.
8. Packet/output retention and redaction policy for protected local content.

Packages must not invent answers to these questions. Where a question does not
block a bounded contract or fixture, record it as deferred configuration and
continue without selecting a model or resource owner.

## 9. Explicit campaign non-goals

- No Grace runtime implementation in GRC-003.
- No migration creation or database schema change.
- No final home or high model selection or benchmark.
- No hardcoded GPU ownership or topology coupling.
- No redesign of CME, Campaign Runner, Dispatch, or the entire resident
  architecture.
- No generalized population scheduler beyond the minimum shared-capacity seam.
- No external-provider approval or credential provisioning.
- No automatic silent fallback between cognition tiers.
- No claim that current local provenance or existing similar modules already
  satisfy GRC-002.

## 10. Readiness conclusion

This is a practical implementation roadmap for Grace. The first safe
implementation wave is F1-F4, with F1 and F2 providing the shared contract and
truth boundary, F3 preserving identity, and F4 preventing transcript dumping.
P1/P2 then make escalation policy and capability/resource selection explicit.
E1/E2/E4 provide the minimum home-to-high path; E3 and E5 add approved
external advice and bounded continuity. I1/I2 connect the result to CME and
authority guards. A1-A3 prove source, deterministic fixture, local boundary,
and shared-resident behavior in that order.

The decomposition is READY_FOR_INDEPENDENT_VALIDATION. It is not a claim that
any package is implemented, tested, live-accepted, or running.
