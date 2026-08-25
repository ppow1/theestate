# GRC-004R2V — Final Grace F1 Aggregate Context Bound Revalidation

Package: GRC-004R2V  
Role: C2 independent targeted revalidator  
Date: 2026-08-25

## Verdict

**PASS**

The single remaining GRC-004 blocker is resolved. `operational_state_refs`
now participates exactly once in the authoritative packet-wide aggregate
calculation, and the previous approximately 92,133-character bypass is
rejected.

## Verification basis

Prior revalidation:
`docs/codex-reports/seat-2/GRC-004RV_Cognition_Contract_Repair_Revalidation.md`

Latest repair report:
`docs/codex-reports/seat-3/GRC-004R2_Bounded_Context_Aggregate_Repair.md`

Implementation repository: `ppow1/Riverview`  
Implementation branch: `codex/c484-operator-persistent-service`  
Repair commit: `4d58c5560b5d883ee5a39a690bed1459cd3524f`

The local implementation worktree is at the reported repair commit. The
repair changes only the packet aggregate argument list and focused regression
tests.

## Aggregate calculation

`src/riverview/reasoning/cognition_contracts.py:238` now calls
`_packet_context_total` with:

* objective;
* question;
* operational state references;
* constraints;
* authoritative current-state references;
* evidence references;
* unresolved ambiguity;
* relevant prior decisions;
* known deterministic results;
* home assessment;
* requested output schema; and
* egress policy.

`operational_state_refs` appears exactly once. No other currently defined
packet context-bearing field is omitted from the same helper.

The following are correctly excluded from embedded-context aggregation because
they are typed identity/control or bounded metadata: UUID identity and
lineage fields, cognition tier, correlation, classification, authority
reference, request class, packet digest, optional UUID references, expiry,
budget, and contract version.

Reference collections remain individually bounded and are also included in the
packet-wide total where they carry packet context. No transcript, arbitrary
mapping, or generic unbounded context field exists.

## Independent boundary probes

Using the repaired commit and `MAX_CONTEXT_CHARS = 64_000`:

1. Valid packet below aggregate limit: **PASS** — accepted.
2. Exact 64,000-character boundary: **PASS** — accepted under the current
   inclusive `>` rejection semantics.
3. One character over the boundary: **PASS** — rejected with aggregate-bound
   error.
4. Operational-state references pushing an otherwise legal packet over the
   limit: **PASS** — rejected.
5. 64 individually legal 500-character operational-state references combined
   with near-limit other context: **PASS** — rejected.
6. Normal reference-based packet: **PASS** — remains usable and round-trips.

The prior bypass was independently recreated with 64 individually legal
operational-state references (32,000 characters) and otherwise legal context.
The resulting actual context was 95,999 characters in this probe and
construction failed with:

`RIV-COG-0001: packet context exceeds its aggregate bound.`

This closes the same failure previously observed at approximately 92,133
characters.

## Focused regression suite

Command run:

```text
PYTHONPATH=src python -m pytest -q \
  tests/test_cognition_contracts.py \
  tests/test_provider_neutral_contracts.py \
  tests/test_resident_context.py \
  tests/test_resident_runtime.py \
  tests/test_grace_authority.py \
  ..\tests\test_grace_consultation_loop.py \
  ..\tests\test_autonomous_reason_execute_loop.py \
  ..\tests\test_governed_provider_scheduler.py
```

Result: **83 passed in 6.77s**.

The added tests cover the operational-state bypass and below/exact/over
aggregate boundaries. Existing focused coverage continues to pass for:

* identity preservation and mismatch rejection;
* provider/resource neutrality;
* advisory-only authority;
* truthful live-generation behavior; and
* serialization and reference-based packet use.

Identity regression: **PASS**  
Provider neutrality regression: **PASS**  
Authority regression: **PASS**  
Live-generation regression: **PASS**

## F4 gate

F1 now provides F4 with a complete, bounded packet aggregate across every
currently defined context-carrying collection. F4 does not need to redefine
the aggregate-bound or repair this omission.

F4 contract readiness: **READY**  
Grace implementation readiness: **READY_FOR_NEXT_GRC_PACKAGE**

