# ESTATE-NOTEBOOK-001 Protected-Field Independent Rereview

Date: 2026-08-02
Repository: `ppow1/theestate`
Reviewed corrected commit: `568050325be51185f5169b55ed74a7e6a762fc7a`
Independent worktree: `A:\review-notebook-protected-fields-final-20260802`

PR #515 merged before the original correction. The first correction remained
blocked by the protected-field defect. This reconstructed PR carries the
explicit protected-field enforcement and its independent rereview; no
local-model testing has run.

## Decision

**PASS FOR ISOLATED LOCAL-MODEL TRIAL, WITH CONDITIONS.**

The protected-field authorization defect is corrected and independently
retested. This decision authorizes only a bounded, isolated notebook trial.
It does not authorize operational Estate use, provider onboarding, resident
integration, merge, auto-merge, or institutional acceptance.

## Independent adversarial results

Fresh detached execution reproduced the original attacks:

| Attempt | Result | Rejected paths | State/digest/revision |
|---|---|---|---|
| `authority.merge: false -> true` | rejected | `authority.merge` | unchanged |
| `assigned_worker: worker-a -> worker-b` | rejected | `assigned_worker` | unchanged |
| mixed `status` plus authority escalation | rejected atomically | `authority.merge`, `status` | unchanged |

Each receipt had `status=rejected`, no accepted paths, the current revision,
the current state digest as both pre/resulting digest, and no state mutation.

## Enforcement review

The runtime now recursively diffs the current state against a proposal
candidate. Only the documented mutable paths are permitted. Parent-object
replacement cannot smuggle protected child changes. Worker proposal identity
must match the assigned worker. Status archival/stale/conflicted transitions,
blocker erasure without observed resolution, stage rollback, evidence deletion,
and unresolved-failure erasure are rejected.

Accepted receipts list exact changed leaf paths and include prior/resulting
digests, revision, observed facts, and provenance. Rejected proposals cannot
produce success receipts or partial state updates. Replay, duplicate update,
stale prior digest, corruption, and interrupted-write behavior remains covered.

## Validation

- Focused notebook tests: **41 passed**.
- Relevant Estate integration tests: **18 passed**.
- Schema meta-validation: **4 passed**.
- Generated state, handoff, receipt, and proposal schema instances: **4
  passed**.
- Fresh-process proof: **passed**; 3 independent processes, 5 receipts, 2
  handoffs, unchanged fixture, exact classification
  `HARNESS-LEVEL FRESH-SESSION CONTINUITY`, `model_invoked=false`.
- Python compilation: passed.
- JSON parsing: 18 evidence/workspace files passed.
- Markdown consistency: passed.
- `git diff --check`: passed.

## Conditions and boundaries

The local-model trial must use a new isolated workspace, exact model-tag
verification, bounded stages, fresh sessions, independent validation, and no
Estate provider registration. The notebook remains subordinate to repository
canon, authorization, worker assignment, Dispatch, PTM, validation, receipts,
reconciliation, provider readiness, and institutional records.

Operational Estate use: **not ready / not accepted**.
Resident integration: **not run**.
Institutional acceptance: **`not_granted`**.

No active Estate runtime, benchmark workspace, model, provider registry,
Open WebUI, Grace, Helen, Dispatch, PTM, or institutional record was modified.
