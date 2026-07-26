# WP-4218 staged backlog reconciliation engine

This directory is the complete removable staging boundary for WP-4220. It produces an
**advisory, non-canonical** read model for future WP-4219 consumption. It does not schedule,
dispatch, assign, merge, mutate Git, update lifecycle records, validate institutionally, or
install anything.

## Architecture and canonical inputs

The cycle is `discover → normalize → correlate → classify → graph → risk/readiness → render
→ validate`. The offline v1 adapter accepts explicit JSON snapshots conforming to
`schemas/source_snapshot_v1.schema.json`; locators and SHA-256 digests preserve provenance.
Repository Parking Lot, WIP, package, receipt, validation, commit, and PR facts must be
exported by a separately governed read-only adapter. Missing host facts remain absent/unknown.
Generated examples are never inputs.

Optional `wp4214_adapter`, `wp4215_adapter`, and `wp4217_adapter` objects carry versioned
references only. Their absence does not stop reconciliation and never triggers a local
reimplementation.

## Evidence and precedence

Precedence is: ambiguity → explicit full supersession → duplicate → dependency/blocker →
stale → coherent implementation+validation+receipt+merge completion → implementation without
validation → criterion-level partial implementation → Parking Lot captured/promoted → authored
without implementation. Unknown/mixed lanes become review-required. Explicit dependencies
alone affect readiness; cycles and missing dependencies block. A commit or receipt alone is
not completion.

Risk is reason-coded from unknown, broad/shared, and production-runtime touch points. Parallel
safety requires known bounded touch points and non-high risk. Priority is a transparent
readiness baseline plus declared institutional priority minus merge-risk penalty, then stable
risk/identifier tie breaks. Traversal and arrays are sorted. The content hash covers logical
rows, revision, schema, and policy, but excludes the volatile generation timestamp.

## Diagnostic usage

```bash
python collaboration/workstreams/WP-4218/reconcile.py generate \
  --source SNAPSHOT_DIRECTORY --output EXPLICIT_OUTPUT_DIRECTORY --revision COMMIT
python collaboration/workstreams/WP-4218/reconcile.py validate OUTPUT/engineering_queue_v1.json
python collaboration/workstreams/WP-4218/reconcile.py explain OUTPUT/engineering_queue_v1.json --item WP-8001
python collaboration/workstreams/WP-4218/reconcile.py compare RUN_A/engineering_queue_v1.json RUN_B/engineering_queue_v1.json
```

The source and output roots may not overlap. The CLI uses no network or subprocess/Git API and
writes only the two named files below the explicit output root. `explain` reports decisions,
blockers, diagnostics, and provenance; exclusions remain rows with complete/superseded/held
readiness rather than disappearing.

## Failure and operator review

Malformed records or invalid outputs fail closed with exit 2. Different deterministic hashes
return exit 1 from `compare`. Operators review ambiguous identity, probable duplication,
supersession, missing dependencies, stale evidence, broad touch points, and unavailable
optional-provider facts; corrections belong only in the governing source and require a new
snapshot/run. A passing staged validation grants no acceptance.

## Installation, rollback, and removal

A future install package must define production adapters, immutable publication/audit storage,
provider compatibility, security/ownership, migrations, rollback, freshness clocks, richer
criterion mapping, PR/commit snapshots, and acceptance validation. WP-4219 may consume only the
versioned queue read model; it must not copy or mutate it. Rollback today is deletion of this
single workstream and WP-4220 package. No production migration or cleanup exists.
