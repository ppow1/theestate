# GRC-011 — Minimum Shared-Resident Capacity Reservation Seam

Package: GRC-011
Roadmap package: GRC-003-P3 — Minimum shared-resident capacity reservation seam
Role: C2 primary implementation writer
Status: `IMPLEMENTATION_COMPLETE_READY_FOR_VALIDATION`

## 1. Exact authoritative P3 definition

The roadmap defines P3 as making home cognition shareable by multiple residents
without implementing the full future resident scheduler.

Dependencies are accepted P2 plus existing provider-capacity and bounded
scheduler behavior. The owned seam is a resident cognition reservation
adapter, reusing provider capacity/scheduler only through an adapter. The
roadmap names reservation fields for resident, occupant, tier, request,
priority, fairness class, resource candidate, lease/deadline, queue state, and
release reason.

Required scenarios are simultaneous Grace/other-resident demand, identity
isolation, capacity hold/release, expiry recovery, priority/fairness evidence,
and proof that reservation does not dispatch. Acceptance requires that Grace
not permanently own the home resource, another resident can obtain a bounded
request, held capacity is observable/recoverable, and reservation cannot become
execution authority.

Explicit non-goals are the full population scheduler, preemption policy, final
SLOs, model residency optimization, and all-resident migration.

## 2. P2/P3 boundary

P2 remains the accepted capability/resource request and binding adapter. P3
consumes its typed `CapabilityResourceRequest`, available
`CapabilityBindingDecision`, and exact `ProviderResourceCandidate`. P3 does
not alter P2 meaning, select or invoke providers, or create a competing binding
contract.

## 3. Shared-resident and reservation semantics

“Shared-resident” is modeled as multiple resident cognition requests
contending for the same measured P2 candidate capacity. It is not hard-coded
to a GPU, model, provider, machine, or office.

Each reservation has its own UUID and preserves separate resident, occupant,
office, cognition tier, request, correlation, binding configuration, provider,
and resource-participant identities. One reservation consumes exactly one
measured capacity unit; the roadmap does not define arbitrary quantity units.

The adapter records `held_for_capacity`, `released`, or `expired`, a bounded
lease deadline, priority, fairness class, sequence, and release reason.
Equivalent requests are idempotent by caller idempotency key and exact request,
identity, binding, resource, priority, fairness, and lease signature.

## 4. Correspondence and conflict behavior

Reservation requires:

- typed request;
- available P2 binding decision with matching request ID, correlation, and
  policy;
- candidate present in that exact binding decision;
- candidate capability equal to requested capability;
- valid resident/resource/binding identity and bounded lease metadata.

Capacity is checked under one adapter lock. A candidate with capacity one cannot
be held twice; an exhausted candidate fails closed. Cross-resident release,
wrong request, wrong occupant, or wrong office is rejected. Duplicate
idempotency keys with changed parameters are rejected rather than consuming a
second unit.

Priority and fairness class are observable metadata and deterministic snapshot
ordering. P3 does not claim a complete fairness, aging, starvation, or
preemption policy; those remain later scheduler/Steward decisions.

## 5. Persistence, release, expiry, and concurrency

P3 uses the roadmap’s bounded adapter-over-capacity seam and creates no new
authoritative database table or migration. Reservation state is intentionally
ephemeral in this minimum seam; persistence/restart for new P3-owned state is
**NOT APPLICABLE**. The adapter provides authoritative in-process readback,
release, and lease-expiry recovery. Existing durable provider capacity remains
owned by the accepted provider registry. A later scheduler package must own
durable cross-process reservation storage if required by live operation.

Release and expiry are part of this minimum seam because the roadmap requires
hold/release and expiry recovery. Lease duration is bounded to 1–3,600 seconds
and is reduced by an earlier request deadline when present.

Concurrency is **PASS for the P3 seam**: the adapter lock serializes competing
reservations and a real two-thread one-unit contention test produces exactly
one holder. This is not a claim of a multi-process scheduler or distributed
database reservation guarantee; that is outside P3’s explicit minimum scope.

## 6. Authority, provider, and transcript boundaries

The reservation carries existing structured identity and capacity evidence but
does not grant resident, policy, provider, execution, Campaign Runner, lease
fencing, or dispatch authority. There is no dispatch or provider invocation
method. Transcript/model prose is not accepted by any P3 input and cannot
manufacture identity, resource, capacity, ownership, or authority.

Malformed UUIDs, tier values, candidate values, binding mismatch, invalid
capacity, invalid priority/fairness, conflicting idempotency, invalid lease,
and invalid release ownership fail closed.

## 7. Regression results

- F1: **PASS** — cognition contract suite.
- F2: **PASS** — provenance and correspondence suites.
- F3: **PASS** — session identity suite.
- F4: **PASS** — bounded context/current-state suites.
- P1: **PASS** — escalation policy and provenance correspondence suite.
- P2: **PASS** — capability/binding suite; P3 consumes exact P2 objects.

No Campaign Runner, E1, E2, E3, provider adapter, model map, or authority
implementation was changed.

## 8. Exact files and symbols changed

Implementation repository: `ppow1/Riverview`
Implementation branch: `codex/c484-operator-persistent-service`
Implementation commit: `3251993eadd11e0f9d867fde5aabbe1808113c80`

- `src/riverview/reasoning/reservation.py`
  - `ResidentCognitionReservation`;
  - `CapacitySnapshot`;
  - `ResidentCognitionReservationAdapter`;
  - `ReservationState` and `ReservationError`.
- `src/riverview/reasoning/__init__.py`: bounded public exports.
- `tests/test_cognition_reservation.py`: P3 contract, identity, capacity,
  idempotency, release/expiry, priority/fairness, malformed-boundary, and
  concurrent contention tests.

## 9. Tests

Focused P3 plus accepted P1/P2/F1–F4/provider/authority regression command:

```text
134 passed
```

`python -m compileall -q src tests`: **PASS**
`git diff --check`: **PASS**

The tests include valid reservation, exact request/binding/resource
correspondence, wrong resource/binding/request, cross-resident release,
capacity exhaustion, duplicate/conflicting idempotency, expiry recovery,
priority/fairness readback, no dispatch, malformed input, and concurrent
one-unit contention.

## 10. Remaining risks and readiness

P3 intentionally does not provide durable cross-process reservation recovery,
full fairness/aging, preemption, or population scheduling. Those are outside
the accepted minimum package and must not be inferred from this adapter.

The exact P3 seam, tests, and accepted foundation regressions are complete and
ready for independent validation. C2 does not self-validate or accept P3.

`READY_FOR_INDEPENDENT_VALIDATION`
