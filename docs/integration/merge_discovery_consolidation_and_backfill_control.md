# Merge Discovery Consolidation and Backfill Control

WP-0624 adds a canonicalization layer between merge discovery and post-merge audit processing.

## Canonical groups

Discoveries are consolidated by target and work package, then assigned a canonical promoted revision from the strongest evidence record. Evidence precedence is:

1. completion receipt commit
2. implementation commit
3. merge commit
4. proposal or pending-package commit
5. commit-message-only inference

Weaker discoveries are marked `superseded` and retain a `superseded_by` link to the canonical discovery. Ambiguous records remain blocked and are not admitted.

## Backfill modes

`merge-discovery scan` and `merge-discovery consolidate` support:

- `observe`: report canonical candidates without creating requests.
- `quarantine`: default first-run mode; canonical candidates are quarantined.
- `admit`: create pending audit requests up to `max_requests_per_cycle`.

The default limits are `max_commits=50`, `max_age_hours=48`, `max_candidates=20`, `max_requests_per_cycle=5`, and `minimum_evidence_level=implementation`.

## Request reconciliation

`merge-discovery reconcile-requests` groups existing audit requests, retains the strongest request per group, and marks weaker active requests as `superseded` while preserving request history.

## Runtime boundary

Operations Runtime admits canonical requests only when merge discovery is explicitly run through the runtime with audit processing enabled. Provider execution and dispatch execution remain false.
