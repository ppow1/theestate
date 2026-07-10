# Steward-Local Codex CLI Smoke-Test Procedure

Status: Optional procedure for WP-0509  
Classification: Estate Internal

## Purpose

This procedure describes one bounded, harmless local Codex CLI trial after deterministic WP-0509 validation passes. It is optional and must be initiated manually by the Steward. It must not be run by automated tests or validation recipes.

## Preconditions

1. Working tree is clean.
2. Current branch is at a known main commit recorded in the authorization evidence.
3. Read and write scopes are narrow and explicit.
4. Target work is harmless, such as creating or updating a dedicated temporary smoke-test artifact under an approved path.
5. A Traffic Controller authorization reference exists.
6. A Steward approval reference exists.
7. A valid execution authorization record exists under the existing execution-adapter authorization path.
8. Session preview has been reviewed first.
9. `danger-full-access` is prohibited.
10. Bypass flags are prohibited.
11. Automatic merge is prohibited.
12. Automatic retry is prohibited.
13. Manual review of result and changed files is required.
14. Manual validation is required after provider completion.

## Suggested Harmless Target

Use a dedicated temporary artifact such as:

```text
docs/demonstrations/steward_local_codex_smoke_test.md
```

Only this path should be writable for the smoke test.

## Inspect Status

```bash
git status --short
git rev-parse HEAD
PYTHONPATH=src python -m estate.cli.main execution-dispatch inspect --dispatch-id <dispatch-id> --json
PYTHONPATH=src python -m estate.cli.main execution-adapter-handoff inspect --dispatch-id <dispatch-id> --json
```

Abort if the tree is dirty, the commit is not the authorized commit, or scopes are broader than approved.

## Preview

```bash
PYTHONPATH=src python -m estate.cli.main execution-session preview --dispatch-id <dispatch-id> --authorization <authorization-json> --json
```

Review the preview. Confirm that `live_provider_called` is false and that the next operations are exactly lease acquisition, one provider call, result persistence, reconciliation, lease release, and report publication.

## Approval Checkpoint

Do not continue unless the Steward explicitly approves the live smoke test after reviewing preview evidence. Record the Steward approval reference and Traffic Controller authorization reference in the authorization record.

## Start Exactly One Live Trial

```bash
PYTHONPATH=src python -m estate.cli.main execution-session start --dispatch-id <dispatch-id> --authorization <authorization-json> --confirm-live-execution --json
```

The authorization must use `read-only` or `workspace-write` only. It must not use `danger-full-access`, bypass flags, automatic merge, or automatic retry.

## Expected Runtime Artifacts

```text
runtime/execution_adapters/authorizations/<authorization-id>.json
runtime/execution_adapters/executions/<dispatch-id>.json
runtime/execution_adapters/attempts/<attempt-id>.json
runtime/execution_adapters/results/<adapter-request-id>.json
runtime/execution_adapters/reconciliation/<dispatch-id>.json
runtime/execution_adapters/reports/<session-id>_session.md
runtime/execution_activity/current.json
```

## Cancellation and Recovery

Inspect the active attempt:

```bash
PYTHONPATH=src python -m estate.cli.main execution-attempt status --dispatch-id <dispatch-id> --json
PYTHONPATH=src python -m estate.cli.main execution-attempt recovery --dispatch-id <dispatch-id> --json
```

If cancellation is required, use the existing execution-attempt cancellation controls only. Do not kill unrelated processes and do not release stale leases without explicit review.

## Reconciliation Checks

```bash
PYTHONPATH=src python -m estate.cli.main execution-result-reconciliation inspect --dispatch-id <dispatch-id> --json
PYTHONPATH=src python -m estate.cli.main execution-session status --session-id <session-id> --json
PYTHONPATH=src python -m estate.cli.main execution-session report --session-id <session-id>
```

Confirm that provider completion is evidence only and that institutional acceptance remains not granted.

## Validation Checks

Run only the validation commands approved for the harmless smoke-test work package. Review changed files manually before any commit or merge decision.

## Cleanup Guidance

If the smoke-test artifact is intended to be temporary, remove it manually after review using normal git workflow. Do not auto-clean, auto-reset, auto-stash, auto-merge, or auto-accept.

## Abort Criteria

Abort immediately if any of the following occurs:

- working tree is unexpectedly dirty before start;
- authorization references are missing;
- preview fails or calls a provider;
- scopes include unapproved paths;
- sandbox is `danger-full-access`;
- bypass flags are present;
- Codex attempts automatic merge, retry, or unapproved writes;
- changed files exceed approved scope;
- the result cannot be reconciled;
- institutional acceptance is implied by tooling instead of a human decision.
