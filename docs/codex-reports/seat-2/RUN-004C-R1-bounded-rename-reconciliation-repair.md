# RUN-004C-R1 Bounded Rename Reconciliation Repair

## Result

Repair status: `REPAIR_COMPLETE_READY_FOR_VALIDATION`

Implementation was committed directly to `ppow1/Riverview` `main`.

- Defect: `RIV-REC-0004`
- Implementation commit: `e5e3247c6d6d974413fd12423981cee1ffef26a2`
- `origin/main`: `e5e3247c6d6d974413fd12423981cee1ffef26a2`
- Named branches created: none

## Preserved GRC-012 repair

The preserved E1 repair worktree is:

`A:\Riverview\main-reconcile`

Recorded state before Campaign Runner changes:

- detached at `fb117209beb2ca26dd249e5fbcd6fe0d2049e6bd`
- staged evidence modification: `docs/operations/roadmap/evidence/GRC-012-E1-writer-evidence.md`
- staged rename: `tests/test_home_cognition.py` to `tests/test_e1_home_cognition.py`
- no files were changed, cleaned, reset, committed, or published there

Preserved E1 repair: `INTACT`

## Root cause

`ResultReconciler.reconcile_repository` derived the authoritative changed paths
from `git diff --name-only`, flattening a rename into the old and new paths.
The authorization check then evaluated each path independently against the
original allowed path set. The authorized old test path passed, but the
replacement destination was treated as an unrelated added file. The same
flat-set assumption was used by the bounded adapter path check.

This was not a valid reason to loosen equality into unrestricted subset or
superset acceptance.

## Repair

`src/riverview/autonomy/control.py` now obtains authoritative rename
correspondence from Git at both boundaries:

- `_worktree_rename_pairs` reads bounded worktree rename pairs.
- `_git_rename_pairs` reads commit-level rename pairs with Git's 20% rename
  detection threshold.
- `_outside_scope` authorizes a rename only when all of the following hold:
  - old and new paths are both authoritative changed paths;
  - the old path is within the authorized path envelope;
  - the old path is unique and the destination is unique;
  - neither path is absolute or contains traversal components;
  - source and destination remain in the same directory/package scope.

All non-rename changed paths still require the existing exact allowed-path
authorization. Unrelated additions, deletions, cross-component movement,
ambiguous replacements, and path traversal remain rejected.

The verified rename pairs are retained in reconciliation validation evidence
and the `execution.reconciled` River event payload, preserving durable
old-path/new-path evidence.

## Tests

Added to `tests/test_autonomy_control.py`:

- authorized rename accepted;
- authorized rename with legitimate content repair accepted;
- Git worktree rename detection;
- commit-level rename correspondence;
- unrelated source/destination rejection;
- cross-package destination rejection;
- unrelated third-file rejection;
- path traversal rejection;
- duplicate/ambiguous replacement rejection;
- ownership-widening rejection.

Focused reconciliation suite: **31 passed**.

Compile/import validation: **PASS**.

## Regression status

- Campaign Runner reconciliation repair: **PASS**
- RUN-003 fencing and authority code: unchanged and regression-covered
- RUN-004 lifecycle and one-go code: unchanged
- writer/validator and repair/revalidator independence: unchanged
- evidence-bound acceptance, history, restart/resume, stale-result handling,
  objective isolation, bounded execution, failure safety, and downstream
  gating: unchanged

The broader PostgreSQL run reproduced the known accumulated expired-row/shared
database contamination in existing lease/lifecycle tests. This was not caused
by the rename repair and was not modified in this package.

## Scope

Only these implementation files changed:

- `src/riverview/autonomy/control.py`
- `tests/test_autonomy_control.py`

The preserved GRC-012 worktree was not consumed. E1 must remain paused until
independent validation of RUN-004C-R1 passes.
