# GRC-008R2 — Empty Current-State Fail-Closed Repair

Package: GRC-008R2  
Roadmap package: GRC-003-F4 — Bounded resident reasoning packet / context assembly  
Role: C2 targeted F4 repair writer  
Date: 2026-08-25

## Repair status

**REPAIR_COMPLETE_READY_FOR_REVALIDATION**

C2 does not accept this repair. It is ready for independent revalidation.

## 1. GRC-008RV remaining blocker

GRC-008RV found that the authoritative F4 projector accepted a mandatory
`current_assignment` item when its value was `{}`. The existing predicate
checked only that the value was mapping-shaped and that the item had a source
reference. That allowed a structurally present but semantically empty object
to satisfy the required-current-state invariant.

## 2. Root cause

In `ResidentReasoningPacketAssembler.assemble`, current-state selection used:

```python
item.layer == "current_assignment"
and item.mandatory
and isinstance(item.value, Mapping)
```

An empty mapping therefore qualified, and its source reference was projected
even though it contained no assignment material.

## 3. Exact semantic-empty condition

The repair defines a meaningful current assignment using the existing
`AssignmentContext` contract. A current-assignment mapping must contain both:

- a non-blank string `objective_ref`; and
- a non-blank string `instruction`.

These are the required assignment fields in `AssignmentContext`. Optional
fields such as `stage_ref`, `authority_ref`, expected output, constraints,
artifacts, and collaborators remain optional. Non-mappings, `{}`, mappings
with blank required values, and mappings containing only provider metadata are
treated as absent and fail with `current-state-missing`.

## 4. Repair

`src/riverview/reasoning/context_assembler.py` now uses the bounded helper
`_meaningful_current_assignment` in the authoritative current-state predicate.
The check remains at the F4 projector boundary, before packet construction and
F1 serialization. No state is inferred from transcript, provider, model,
resource, or source-reference text.

## 5. Tests added

`tests/test_reasoning_context_assembler_repair.py` now independently verifies:

1. `current_assignment = {}` is rejected with `current-state-missing`;
2. a mapping containing only `provider_ref` is rejected as non-authoritative;
3. the existing valid populated assignment path remains accepted; and
4. the existing aggregate-bound regression remains enforced.

## 6. Original wrong-resident regression

**PASS.** The existing targeted regression still rejects a request resident
that differs from the authoritative bundle resident before packet emission.

## 7. Original missing-current-state regression

**PASS.** The existing targeted regression still rejects a bundle with no
`current_assignment`, including transcript/provider-only substitutes.

## 8. Valid current-state regression

**PASS.** A bundle produced from the valid `AssignmentContext` fixture still
assembles into an F1-compatible packet and retains operational-state
references.

## 9. F1 regression

**PASS.** The focused integrated run retained F1 contract, identity, aggregate
bound, operational-state reference, provider-neutral, authority, and
serialization coverage. The 64,000-character bound remains unchanged.

## 10. F2 regression

**PASS.** The focused integrated run retained provenance, exact request/result
correspondence, failure-provenance, serialization, and repair-correspondence
coverage. No provenance code was changed.

## 11. F3 regression

**PASS.** The focused integrated run retained cognition-session identity,
session/request separation, stale-context, persistence, and serialization
coverage. No session code was changed.

## 12. Provider-neutrality regression

**PASS.** The repair adds no provider, model, endpoint, GPU, or resource
selection. Provider metadata cannot satisfy the current-state predicate.

## 13. Authority-boundary regression

**PASS.** The repair only validates current-state material. It does not create,
widen, or execute authority.

## 14. Exact files and symbols changed

Implementation repository: `ppow1/Riverview`  
Branch: `codex/c484-operator-persistent-service`  
Implementation repair commit: `4f41dc4f765fa95babc1342ae63d05d049f402e3`

Changed files:

- `src/riverview/reasoning/context_assembler.py`
  - added `_meaningful_current_assignment`;
  - applied it in `ResidentReasoningPacketAssembler.assemble`.
- `tests/test_reasoning_context_assembler_repair.py`
  - added empty-mapping and provider-only semantic-empty regressions.

No migration, F1, F2, F3, P1, P2, Campaign Runner, provider, model, GPU, or
unrelated runtime files were changed.

## 15. Validation evidence and readiness

The focused integrated selection covering F4, F1, F2, F3, provider neutrality,
resident context/runtime, Grace authority, and adjacent Grace tests passed:

```text
137 passed in 6.96s
```

`python -m compileall -q src tests`: **PASS**  
`git diff --check`: **PASS**

The broad unfiltered suite remains subject to the previously known unrelated
optional `mcp` collection dependency; this targeted repair does not depend on
that suite.

The scoped implementation was published to the implementation branch. The
repair is **READY_FOR_INDEPENDENT_REVALIDATION**.
