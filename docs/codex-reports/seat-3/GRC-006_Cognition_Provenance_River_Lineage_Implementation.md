# GRC-006 — GRC-003-F2 Cognition Provenance and River Event Lineage

Package: GRC-006  
Roadmap package: GRC-003-F2 — Cognition provenance and River event lineage  
Role: C3 primary implementation writer  
Implementation status: IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION  
Date: 2026-08-25

## 1. Exact authoritative F2 definition

The accepted GRC-003 roadmap defines GRC-003-F2 as follows.

Objective: make every cognition attempt, escalation, result, unavailable
outcome, and integration continuation distinguishable from deterministic work.

Dependencies: F1 for field vocabulary and the existing River event contracts.

Files/symbols expected to be touched: `Riverview/src/riverview/river/events.py`,
`river/store.py` only where bounded payload validation is required, a new
provenance/event helper under `Riverview/src/riverview/reasoning` or `river`,
`Riverview/tests/test_river_event.py`, and a new cognition provenance test.

Existing seams to reuse: `RiverEvent` aggregate/correlation/causation/
idempotency/classification, the Artifact Provenance Model for artifact
references, and existing operational event fields for provider IDs.

New components if required: a `CognitionProvenance` envelope with actor class,
resident/occupant/office, tier, implementation, provider, resource class,
request/correlation, packet, policy, live-generation, result/failure status,
and evidence references; plus event types for requested, admitted, held,
started, completed, unavailable, rejected, timed_out, and integrated.

Database/persistence impact: no migration unless existing River event payload
cannot carry the validated fields. If persistence is required, define an
additive versioned event/payload change and defer migration creation to a
separately accepted package.

Required tests: deterministic event with `live_generation=false`; Grace
home/high events with true; external/worker/validation/Steward actor classes;
correlation and causation; idempotency; resident mismatch; and no-result/
no-generation truth.

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

Downstream dependencies in the accepted graph include E2 and E3, which depend
on F2 for high/external request lineage; I1, which depends on F2 for CME
cognition integration; I2 and the later A1/A2/A3 acceptance chain.

## 2. GRC-005 classification correction

Independent GRC-005V correctly found no blocking behavioral defect in the
submitted bounded packet assembler. It found a blocking roadmap-classification
defect: the accepted roadmap labels bounded packet assembly as GRC-003-F4,
not F2. Therefore:

- GRC-005 implementation is technically validated but roadmap-misclassified;
- GRC-005V correctly identified it as F4-shaped work;
- GRC-006 implements the actual accepted GRC-003-F2 provenance package.

The early-F4 implementation at commit
`dab860cd8eb02b6333fbade67f6a63abb8887181` was preserved. No GRC-005 files
were deleted or broadly rewritten, and F4 is not claimed accepted by this
package. Its final F4 acceptance remains dependent on the accepted roadmap
prerequisites and independent F4 validation.

## 3. River/EventStore seams discovered and reused

The inspected River foundation provides:

- immutable, frozen `RiverEvent` records;
- event IDs and timezone-aware occurrence timestamps;
- aggregate type/ID streams;
- separate correlation and causation UUIDs;
- idempotency keys;
- River classification;
- detached immutable payload mappings; and
- `EventStore.append` idempotency reconciliation plus
  `read_aggregate` sequence-ordered persistence reads.

The existing `river_events` migration already stores all required River
identity/correlation/causation/payload/timestamp fields as JSONB and indexes
aggregate sequence and correlation. The F2 envelope therefore fits the
existing persistence shape. No migration, new table, duplicate event store,
or in-place history mutation was introduced.

## 4. Implementation architecture

Added `reasoning.provenance` with:

- `CognitionProvenanceEventType`: requested, admitted, held, started,
  completed, unavailable, rejected, timed_out, and integrated;
- `CognitionProvenance`: versioned bounded typed payload and F1 request/result
  factories;
- `CognitionProvenanceWriter`: append/idempotency/conflict guard and
  aggregate reconstruction;
- `ProvenanceLineageError`: fail-closed validation error.

`CognitionProvenance.for_request` integrates F1
`CapabilityResourceRequest`; `for_result` integrates F1 `CognitionResult`.
`validate_against_request` compares request/packet, correlation, resident,
occupant, office, implementation, authority, tier, classification, and source
event correspondence where available.

The writer maps each record to an immutable `RiverEvent` with aggregate
`cognition_request` and aggregate ID equal to the exact request ID. The source
event remains an explicit payload field; causation remains a separate River
causation field. Result/integration/failure events require an already recorded
request event in that aggregate, preventing floating results.

## 5. Event/provenance model and truthfulness

Every payload includes schema version, provenance event ID, event type, actor
class, resident/occupant/office/implementation IDs, authority reference,
source event, request/correlation/causation, optional tier/provider/resource/
packet/result/policy references, status/failure code, classification,
live-generation, evidence/state references, and occurrence timestamp.

Deterministic request events use `DETERMINISTIC_SUBSTRATE` and
`live_generation=false`. Grace home/high and external live results require the
matching cognition tier and observed provider/resource references. Non-Grace
worker, engineering-validation, and Steward actor classes remain distinct and
cannot claim live generation. Unavailable, rejected, and timed-out outcomes
retain failure codes and never become completed success.

Provider/resource fields are observations copied from an F1 result when
present. They do not select a provider, model, endpoint, GPU, or resource.

## 6. Lineage, correlation, causation, and identity

Correlation identifies the cognition workflow. Causation identifies the direct
prior event when one exists. The source event is separately retained so a
request can point to the authoritative event that caused cognition without
collapsing source identity and direct causal sequencing.

Aggregate reconstruction reloads the ordered River payloads after process
restart and verifies request ID, correlation, resident, occupant, and office
identity consistency across the stream. Duplicate idempotent writes return the
existing event; a same-event conflicting payload fails closed.

Identity is supplied by typed IDs and F1/context seams. Transcript text,
result prose, provider/model/GPU/endpoint metadata, implementation class, and
office display text are never used as identity. Authority is a reference only;
the provenance envelope contains no execution authorization field.

## 7. Persistence/restart and failure behavior

The implementation uses the existing durable `EventStore` protocol and River
JSONB payload persistence. No in-memory lineage is authoritative. The tests
use a restart-surviving store double implementing the same append/read
contract to verify serialization and aggregate reconstruction; the existing
River event contract tests continue to pass. Live database acceptance remains
outside F2 and is not claimed here.

Fail-closed cases include missing source event, missing actor/tier observation,
missing correlation, cross-resident or cross-office correspondence, missing
request lineage, malformed payload/version, invalid event type, false
deterministic/live-generation claims, missing failure code, and duplicate
conflicting payload.

## 8. Files and symbols changed

Implementation repository: `ppow1/Riverview`  
Branch: `codex/c484-operator-persistent-service`

Changed files:

- `Riverview/src/riverview/reasoning/provenance.py`
- `Riverview/src/riverview/reasoning/__init__.py`
- `Riverview/tests/test_cognition_provenance.py`

Existing `river/events.py`, `river/store.py`, F1 contracts, and the early-F4
assembler were preserved without modification. No Campaign Runner files,
schema, lifecycle, or reports were changed.

## 9. Tests and F1 regression evidence

Focused F2 tests cover request event durability, identity/source lineage,
exact result correspondence, unrelated-request rejection, source/request/
result reconstruction, correlation and causation serialization, timestamps,
idempotency/conflicting duplicate payloads, unavailable truth, deterministic
no-generation truth, home/high/external observations, worker/validation/
Steward actor distinction, authority boundary, transcript/result-prose
non-identity, provider/resource neutrality, and malformed/missing lineage.

Required F1, River, resident, authority, and adjacent Grace/provider suites:

`102 passed in 6.09s`

Compileall and package import validation also passed. Existing F1 identity,
bounded-context including `operational_state_refs`, provider neutrality,
advisory authority, and live-generation truth tests remain passing.

## 10. Explicit non-goals

This package does not implement event-producing cognition orchestration,
provider execution, home/high/external routing, resource scheduling, policy
selection, session runtime, F4 assembly redesign, migrations, model selection,
GPU assignment, CME integration, Campaign Runner changes, or live model
acceptance.

## 11. Readiness and next dependency

F2 is implemented and tested against the accepted F1 vocabulary and existing
River persistence seam. Independent validation must inspect the actual source,
event payloads, idempotency/conflict behavior, reconstruction tests, and scoped
diff, while keeping IMPLEMENTED, TESTED, LIVE-ACCEPTED, and RUNNING separate.

The next roadmap dependencies are F3 identity-preserving cognition session
boundary and the policy/provider/execution packages according to the accepted
graph. The early-F4 assembler remains available but cannot be finally accepted
until its F1/F2/F3 prerequisites and F4 acceptance criteria are independently
validated.

`IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION`
