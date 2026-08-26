# ESTATE-NOTEBOOK-001 Protected-Field Correction Report

Date: 2026-08-02
Repository: `ppow1/theestate`
Starting `origin/main`: `9ae35bb6666eaed5fbea895f5892afa6864165ff`
Authoring branch: `agent/notebook-protected-fields`
Starting head: `034f4110375098ed13daf507e961a8e8807c6509`

## Root cause

The prior correction validated the proposal envelope but did not constrain
`proposal["changes"]` to a mutable field set. `apply_verified_update()` copied
every proposed top-level key into the verified state. A worker could therefore
replace `authority`, `assigned_worker`, `constraints`, or other protected
fields and receive an accepted receipt.

## Correction

`engineering_notebook.py` now builds a candidate state, computes recursive
changed paths, and rejects the entire proposal unless every changed leaf is in
the explicit allowlist below. Parent-object replacement cannot bypass child
checks. Proposal worker identity must equal the current assigned worker.

### Exact mutable-path allowlist

```text
task.current_stage
task.stage_status
task.completed_stages
task.remaining_stages
task.next_action
task.current_blocker
task.blocking_severity
task.repair_count
evidence.files
evidence.last_results
evidence.unresolved_failures
evidence.test_counts
evidence.schema_state
evidence.compilation_state
evidence.fixture_integrity
evidence.receipts
continuity.previous_session
continuity.handoff_reason
continuity.compaction_summary
continuity.safe_facts
continuity.omitted_information
continuity.next_stage_files
status
```

These are observed working-state facts only. `status=completed` remains gated
by terminal task state, artifacts, required validation, and no blockers.
`status=archived`, `stale`, and `conflicted` remain outside worker control.

### Protected-field policy

Every path outside the allowlist is protected, including identity, schema and
objective identity, assigned worker/provider, source commit/digests, authority
and merge/destructive/network/Dispatch permissions, provider readiness, read
and write scope, repository/workspace/benchmark/model identity, retry and
validation policy, architecture/protected interfaces, provenance, timestamps,
audit IDs, and institutional acceptance. Nested changes and deletion of
required protected children are rejected by recursive path comparison.

## Receipt integrity

Rejected receipts contain exact changed/rejected paths, proposal identity,
current revision, current state digest, unchanged resulting digest, and
`status=rejected`; the state is not mutated. Mixed proposals are rejected as a
whole. Accepted receipts list exact changed leaf paths, use
`prior_state_digest` as the pre-state digest, include the resulting digest and
revision transition, observed facts, and provenance entries.

## Tests and validation

- Focused notebook tests: **41 passed**.
- Relevant Estate integration tests: **18 passed**.
- Adversarial coverage includes authority, worker/provider/model identity,
  institutional acceptance, repository/workspace/scope, source commit/digest,
  retry and validation policy, nested protected mutations, deletion/type
  mutation, mixed updates, blocker erasure, false completion, rejected replay,
  duplicate accepted updates, stale/conflicted updates, corruption recovery,
  exact receipts, and byte-for-byte state preservation.
- Fresh-process proof: **passed**; 3 independent sessions, 5 receipts, 2
  handoffs, unchanged fixture, `HARNESS-LEVEL FRESH-SESSION CONTINUITY`, no
  model invoked.
- Schema meta-validation: **4 passed**.
- Schema instance validation: state, handoff, receipt, and update proposal
  **4 passed** using file-based resolution for relative schema references.
- Python compilation, JSON parsing of 18 evidence/workspace files, and
  `git diff --check`: **passed**.

The receipt schema now requires provenance and the proposal schema documents
the same mutable-path set as `x-mutable-paths`. Generated proof receipts and
packets were refreshed so evidence remains schema-valid.

## Boundaries

No active Estate runtime, resident surface, provider registry, model, Open
WebUI, Dispatch, PTM, benchmark workspace, or institutional record was
modified. Qwen3-Coder testing was not run. Institutional acceptance remains
`not_granted`.
