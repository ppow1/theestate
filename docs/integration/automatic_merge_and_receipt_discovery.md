# Automatic Merge and Receipt Discovery

WP-0623 adds a local, evidence-only front end for the post-merge audit loop. The discovery runtime scans configured operational targets, observes recent local Git commits and completion receipts, correlates work-package identity, records normalized discovery artifacts, and creates compatible post-merge audit requests.

## Boundary

Merge discovery is observation and request generation only. It does not merge, commit, repair, approve, execute providers, dispatch work, or perform Steward acceptance.

## Artifacts

- Cursor: `runtime/merge_discovery/targets/<target_id>/cursor.json`
- Discovery records: `runtime/merge_discovery/discoveries/*.json`
- Candidate records: `runtime/merge_discovery/candidates/*.json`
- Status: `runtime/merge_discovery/status/latest.json`
- Audit requests: `runtime/post_merge_audit/requests/*.json`

## Correlation order

1. `work_package_id` from a completion receipt.
2. Work-package ID in the completion-receipt filename.
3. Work-package ID in the commit message.
4. Work-package ID in changed pending/completion paths.

Conflicting IDs are recorded as `ambiguous` and no audit request is created.

## Deduplication

Discovery suppresses duplicate audit request creation for the same target, work package, and source commit. It also suppresses requests when an existing final post-merge verdict is already present for the same work package and target.

## CLI

```bash
python -m estate.cli.main merge-discovery scan --target estate-main --json
python -m estate.cli.main merge-discovery status --target estate-main --json
python -m estate.cli.main merge-discovery candidates --target estate-main --json
python -m estate.cli.main merge-discovery replay --target estate-main --max-commits 50 --json
python -m estate.cli.main operations-runtime run-once --discover-merges --process-audits --json
```

## Office visibility

The Office status bar includes merge discovery availability, last scan time, last scanned commit, merge scan metrics, pending and ambiguous candidates, latest discovered work package, latest created audit request, and duplicate suppression count.
