# GRC-006RV — Provenance Correspondence Repair Revalidation

Package: GRC-006RV  
Roadmap package: GRC-003-F2 — Cognition provenance and River event lineage  
Role: C2 independent repair revalidator  
Date: 2026-08-25

## Verdict

**PASS**

The original GRC-006V blocking defect is resolved. The repaired durable writer
loads the canonical persisted `cognition.requested` event and validates every
request-bound downstream event before calling `EventStore.append`. Independent
memory-store and real PostgreSQL probes rejected all six original substitutions
without changing the aggregate. Valid results and failure outcomes remain
recordable, durable, and reconstructable.

## Commit and repair verification

Implementation repository: `ppow1/Riverview`  
Implementation branch: `codex/c484-operator-persistent-service`  
Original implementation commit: `2a04ce0b2977814baac4d8896467c92e1c3b9bfc`  
Repair implementation commit: `005f953f63975ae83a1d61291ee1dbe9d80bf74a`

The implementation worktree was on the reported branch and repair commit.
The repair diff is bounded to `src/riverview/reasoning/provenance.py` and
provenance tests. No F3, F4, River replacement, migration, or unrelated
runtime work was introduced.

## 1. Durable canonical-request enforcement

`CognitionProvenanceWriter.record` now handles every non-request event by:

1. reading the request aggregate from the injected EventStore;
2. finding exactly one stored `cognition.requested` event;
3. reconstructing its typed `CognitionProvenance` payload;
4. rejecting missing, ambiguous, or malformed request lineage; and
5. invoking `validate_against_request` against that durable canonical request
   before `EventStore.append`.

This is an authoritative durable-writer gate, not an optional caller-side
check or process-local cache. The typed validator compares request ID,
correlation ID, resident, occupant, office, implementation, authority,
source-event ID, cognition tier, classification, and the canonical packet ID
when present.

Stored-request lookup: **PASS**

## 2. Six original attacks

After recording a valid canonical request, independent probes attempted
downstream events with substituted resident, occupant, office, implementation,
authority, and source-event identities. Every case was rejected with the
corresponding mismatch error. In each case the in-memory aggregate remained at
one event, so no forged River event was appended.

| Probe | Result |
|---|---|
| resident mismatch | REJECTED; aggregate unchanged |
| occupant mismatch | REJECTED; aggregate unchanged |
| office mismatch | REJECTED; aggregate unchanged |
| implementation mismatch | REJECTED; aggregate unchanged |
| authority mismatch | REJECTED; aggregate unchanged |
| source-event mismatch | REJECTED; aggregate unchanged |

The same six probes were repeated against the real PostgreSQL EventStore.
Output showed six rejections, followed by `POSTGRES_FORGED_CHECK 1
['cognition.requested']`. The canonical request remained unchanged after
reload.

Original correspondence defect: **RESOLVED**  
Resident mismatch rejection: **PASS**  
Occupant mismatch rejection: **PASS**  
Office mismatch rejection: **PASS**  
Implementation mismatch rejection: **PASS**  
Authority mismatch rejection: **PASS**  
Source-event mismatch rejection: **PASS**  
Forged-event persistence prevention: **PASS**

## 3. Valid and failure paths

A matching result was accepted, persisted, and reconstructed after creating a
new EventStore/writer. The real PostgreSQL probe reported:

`POSTGRES_VALID_RELOAD 2 ['cognition.requested', 'cognition.completed'] True`

Unavailable, rejected, and timed-out events also passed through the same
correspondence gate when their request-bound identity matched. A forged
failure outcome was rejected and did not advance the aggregate.

Valid lineage: **PASS**  
Failure provenance: **PASS**  
Persistence/restart: **PASS**

## 4. Correlation, causation, and idempotency

The repair preserves separate River correlation and causation fields. Valid
request-to-result ancestry remains reconstructable; the repair does not require
correlation and causation to be identical. Existing idempotent repeats and
conflicting duplicate behavior remain covered by the focused suite, with
correspondence checked before append.

Correlation/causation regression: **PASS**  
Idempotency/conflict regression: **PASS**

## 5. Regression areas

Previously passing F2 areas remain intact:

- Provider neutrality: **PASS** — no provider, model, endpoint, or GPU
  selection was introduced.
- Authority boundary: **PASS** — `authority_ref` remains a reference and does
  not grant execution authority.
- Live-generation truth: **PASS** — deterministic and failure events retain
  truthful non-live semantics.
- F1 regression: **PASS** — identity, bounded context,
  `operational_state_refs` aggregate inclusion, provider neutrality, authority,
  and live-generation tests remain passing.
- Early F4 preservation: **PASS** — the earlier bounded packet assembler was
  not modified or accepted by this repair.

## 6. Independent test evidence

Focused and adjacent regression suite:

`113 passed in 6.26s`

The suite included the new repair tests, provenance, River, accepted F1
contracts, provider-neutral contracts, resident context/runtime, Grace
authority, and adjacent Grace/provider tests. Compile/import validation passed.

Independent probes covered all six substitutions, unchanged aggregate state,
valid result reload, unavailable/rejected/timed-out outcomes, and real
PostgreSQL persistence/reload. The real PostgreSQL forged-event check and
valid-lineage reload both passed.

## 7. Next roadmap package

With F2 correspondence now accepted, the next eligible package remains:

**GRC-003-F3 — Identity-preserving Grace cognition session boundary**

This follows the accepted GRC-003 dependency graph. The early F4 packet
assembler remains separate and does not change F3 eligibility.

Next roadmap package: **GRC-003-F3 — Identity-preserving Grace cognition
session boundary**  
Grace implementation readiness: **READY_FOR_GRC-003-F3**

