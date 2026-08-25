# GRC-011V — P3 Shared-Resident Capacity Reservation Validation

Package: GRC-011V  
Roadmap package: GRC-003-P3 — Minimum shared-resident capacity reservation seam  
Role: C1 independent validator  

## Verdict

**PASS**

Implementation commit validated: `3251993eadd11e0f9d867fde5aabbe1808113c80`

The exact commit implements the bounded P3 reservation adapter over accepted
P2 capability/binding objects. It provides observable in-process holds,
bounded capacity accounting, release, expiry recovery, identity checks, and
idempotency without dispatch, provider selection, execution, or generalized
scheduling.

## Repository and roadmap verification

The implementation commit exists in `ppow1/Riverview`, branch
`codex/c484-operator-persistent-service`, with origin
`https://github.com/ppow1/Riverview.git`. The writer report was read from
`ppow1/theestate`, branch `codex/riverview-bounded-doorbell`, report commit
`8f59f5c0f4e00a9d2f9bb2eb4d7dd4cc9e741494`.

The authoritative P3 card defines a minimum resident cognition reservation
adapter: share home cognition between residents, reuse P2/provider capacity
seams, represent resident/occupant/tier/request/priority/fairness/resource/
lease/release data, support hold/release/expiry and contention evidence, and
never dispatch. It explicitly excludes a general scheduler, preemption, final
SLOs, model residency optimization, and population migration.

P3 roadmap compliance: **PASS**

## Scoped diff and actual implementation

The exact commit changes only:

- `src/riverview/reasoning/reservation.py`
- `src/riverview/reasoning/__init__.py`
- `tests/test_cognition_reservation.py`

No migration, database table, provider invocation, Campaign Runner, E1/E2/E3
runtime file, generated artifact, or environment file is in the commit.

`ResidentCognitionReservation` stores UUID resident, occupant, request, and
correlation identities; office; cognition tier; binding/resource references;
priority; fairness class; one capacity unit; lease deadline; state; release
reason; and sequence. `ResidentCognitionReservationAdapter` implements
`reserve`, `release`, `expire`, `read`, `snapshot`, and `capacity`.

P2/P3 boundary: **PASS**

The adapter requires a typed F1/P2 request, an available
`CapabilityBindingDecision` with matching request/correlation/policy, and a
candidate contained in that exact decision. It does not create a second
provider/resource contract or select a physical resource. Concrete provider
and participant values are observed candidate evidence supplied by P2.

## Independent adversarial and runtime evidence

Independent probes against the exact source passed:

- valid reservation preserved resident, occupant, office, request, resource,
  and held state;
- two residents competing for one measured unit produced one holder;
- twelve concurrent contenders for a three-unit candidate produced exactly
  three holders;
- unrelated request/binding and unrelated candidate were rejected;
- foreign resident release was rejected;
- valid owner release returned capacity;
- expiry changed the reservation to `expired` and restored capacity;
- equivalent idempotency retry returned the same reservation;
- changed parameters under an existing idempotency key were rejected;
- malformed typed/candidate inputs failed closed;
- no `dispatch` or `execute` operation exists on the adapter and reservation
  does not invoke a provider.

Shared-resident contention: **PASS**  
Reservation correspondence: **PASS**  
Capacity/oversubscription: **PASS**  
Idempotency: **PASS**  
Release/expiry: **PASS**

The adapter’s `RLock` encloses idempotency lookup, expiry, held-unit count,
and insertion. The independent multi-thread probes therefore observed no
double admission or oversubscription within the declared in-process P3 seam.
The implementation makes no unsupported multi-process/distributed guarantee.

## Identity, authority, and input boundaries

Reservation identity is copied from the canonical typed request and is checked
against the exact P2 binding and candidate. Release requires matching request,
resident, occupant, and office. Wrong request, wrong binding, wrong candidate,
invalid tier, invalid lease, invalid priority/fairness, and invalid candidate
health/capacity fail closed.

Reservation correspondence: **PASS**  
Authority boundary: **PASS**  
Transcript-not-authority: **PASS**

Reservation is advisory capacity state only. It does not grant resident,
Grace, policy, scheduler, Campaign Runner, lease-fencing, or execution
authority. No transcript, prompt, or model-output field is accepted by the
P3 API.

## Provider/resource neutrality and P3 ownership

Source inspection found no hard-coded GPU IDs, PCIe topology, RTX/P100
assignment, provider, model, endpoint, or machine name. The adapter records
the concrete P2 candidate that was supplied, while the request remains a
capability request. This is the required distinction between provider-neutral
contract behavior and concrete observed resource evidence.

P3 records a bounded hold and lease; it does not implement capacity
reservation persistence, queue dispatch, fairness policy, preemption, or
resource ownership. Priority and fairness class are observable metadata and
deterministic snapshot ordering, not a generalized scheduler.

Provider/resource neutrality: **PASS**  
P3 boundary: **PASS**

## Persistence/restart classification

Persistence/restart classification: **PASS — NOT APPLICABLE**

The P3 card permits an adapter over existing capacity records and states no
production migration is required. This implementation has no database table,
migration, durable reservation record, or cross-process reservation authority;
its reservation map is explicitly an in-process bounded seam. Existing durable
provider capacity remains owned by the accepted registry. Durable
cross-process reservation recovery belongs to a later scheduler/operational
package and is not silently claimed here.

## Predecessor regressions

The targeted regression command covering the P3 tests plus accepted F1, F2,
F3, F4, P1, P2, provider-neutrality, and Grace-authority tests completed with
**63 passed**. The focused P3 module independently completed with **7 passed**.

- F1 regression: **PASS**
- F2 regression: **PASS**
- F3 regression: **PASS**
- F4 regression: **PASS**
- P1 regression: **PASS**
- P2 regression: **PASS**
- Predecessor regression: **PASS**

`python -m compileall -q src tests`: **PASS**.  
`git diff-tree --check` for the implementation commit: **PASS**.

The broad suite was also attempted. Three pre-existing MCP test modules could
not collect because the optional `mcp` package is unavailable. Excluding those
modules, four unrelated engineering-intent tests failed because the isolated
worktree path is not accepted by their repository-root fixture; their failures
occur in `src/riverview/intake/engineering.py`, outside the P3 diff. The
targeted P3 and predecessor evidence is unaffected. These are infrastructure/
fixture limitations, not P3 semantic failures.

## E1/E2/E3 collision assessment

E1/E2/E3 collision: **NONE**

The actual P3 diff owns only the new reservation module, its public exports,
and P3 tests. No upcoming execution implementation file or symbol was
modified. The shared `reasoning/__init__.py` change is limited to additive P3
exports and does not overlap an execution seam.

## Newly unlocked packages

With P3 accepted, the directly dependent roadmap package is:

- **GRC-003-I2 — Authority, failure, and provenance integration guards**,
  after its other dependencies (`E1`, `E2`, `E3`, and `I1`) are accepted.

The immediate execution packages E1, E2, and E3 remain governed by their own
dependencies and are not implemented or accepted by this validation. P3 does
not make Grace Cognition globally complete.

## Final status

P3 final status: **ACCEPTED**

No implementation changes were made by C1.

