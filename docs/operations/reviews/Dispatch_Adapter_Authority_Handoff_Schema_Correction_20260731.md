# Dispatch Adapter Authority Handoff Schema Correction

## Objective

Close the merge-readiness blocker identified in PR #502 by giving the durable
Engineering authorization and Operations decision records closed, versioned
Draft 2020-12 contracts at creation and at the final adapter-handoff boundary.

## Review and correction

- Starting HEAD: `df72c9311cec97ee6a2bb5fd9ac777649a62a02a`.
- Correction commit: `68890218 Add closed authority record schemas`.
- The blocker was that the handoff checked authority-record existence,
  correlation, and digests without validating the complete record shapes.
- Engineering authorization schema: `schemas/engineering/engineering_authorization_v1.schema.json`, ID `estate.engineering.authorization.v1`.
- Operations decision schema: `schemas/operations_control/operations_decision_v1.schema.json`, ID `estate.operations-control.decision.v1`.
- `src/estate/core/authority_schema_runtime.py` provides the canonical
  registry, Draft 2020-12 validation, FormatChecker use, and digest helper.
- Technical Dispatch now creates a deterministic, create-once Operations
  decision for the complete execution evidence chain. The original Grace
  Operations decision remains the parent decision; the new record is not a
  second authorization system.

## Enforcement

Creation constructs the complete record, validates its closed schema, computes
the canonical digest, and only then publishes create-once durable JSON with
flush, fsync, close, and parent-directory durability where supported.

The final handoff bounds and loads the exact authorization and Operations
decision references, validates both schemas through the registry, recalculates
both digests, checks expiry, and correlates Grace, Helen, PTM, Engineering,
Dispatch, provider, adapter, prompt, read scope, write scope, expected outputs,
and cross-references. Schema failures do not publish adapter requests.

Historical and nontechnical records remain readable; historical incomplete
technical Dispatch records remain blocked and are not migrated.

## Validation

- Complete bounded changed-scope matrix: **223 passed**.
- Includes 57 authority-record/schema tests, PR #502 propagation, Grace/Helen,
  PTM, Engineering composition, Dispatch, queue, bridge, local worker,
  provider runtime/catalog, Qwen, and Codex tests.
- Draft 2020-12 schema checks with FormatChecker: passed.
- Registry uniqueness and `$ref` resolution: passed.
- Python compilation, tracked JSON parsing excluding the two known malformed
  fixtures, and `git diff --check`: passed.
- The malformed fixtures reproduce identically on base and head and are outside
  the adapter-handoff path.
- No named Windows path-separator regression was found in the repository.

## Preservation and status

- No live provider, Qwen, Ollama, artifact, receipt, or model was used.
- Institutional acceptance remains `not_granted`.
- Qwen source/configuration, historical Qwen evidence, and failed validation
  evidence were not modified or reused.
- All 16 stashes remain preserved.
- `A:\theestate` remains untouched.
- PR #502 remains open, draft, unmerged, and targets `main`.
- Final pushed HEAD for this correction: `e8b4a65b`.

## Final handoff

The correction is ready for the final merge-readiness audit after commit and
push. The next Steward action is to review that audit and separately authorize
any merge; this correction does not merge or enable auto-merge.
