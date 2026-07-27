# WP-4221 staged Engineering Campaign Dashboard projection

This removable staging boundary implements WP-4219's deterministic, immutable, read-only
data projection. It consumes only a published WP-4220 `estate.engineering-queue/v1` JSON
artifact; it does not discover repository facts, reconcile a backlog, or mutate an authority.

## Architecture and provider contracts

`dashboard_cli.py` loads one explicit queue file, validates its version/identity invariants,
and passes it to a pure projection. The projection preserves each WP-4220 row and provenance,
composes 15 versioned panels, explicit provider states, health values, definition-versioned
metrics, a dependency graph, an immutable snapshot, and a template-based operator summary.
WP-4214 duration, WP-4215 parallel-plan, and WP-4217 Git readiness are used only when WP-4220
publishes references. Missing optional evidence produces `partial` or `unavailable`, never a
substitute estimate, capacity, assignment, repository claim, or favorable zero.

WP-4220 v1 fields consumed are queue/schema/policy versions, generation ID/time/hash, source
revision, advisory flag, ordered rows, lifecycle/readiness, priority, lane, dependency,
blocker, touch-point, risk, parallel group, provider references, evidence, diagnostics, and
provenance. Duplicate row IDs, malformed primary data, or unsupported versions are fatal.

## Snapshot, panels, metrics, and determinism

The snapshot schema is `estate.engineering-campaign-dashboard/v1`; all panel records use the
common `estate.engineering-campaign-panel/v1` envelope. Panel `state` distinguishes `empty`
from `unavailable`. Freshness is `fresh` (at most 24h), `aging` (at most 72h), `stale`,
`unavailable`, or `source_mismatch`; degradation additionally uses `none`, `degraded`,
`partial`, `invalid`, and `unsupported_version` at the relevant boundary.

Metrics declare calculation version, source records, denominator, availability reason, and
evidence completeness. Values not present in WP-4220 v1—duration actuals, completion range,
promotion-time queue age, and lane capacity—remain unavailable. No history is fabricated.

Stable row/edge/group/reason ordering and canonical JSON provide deterministic aggregation.
The content hash covers all logical content and policy/configuration effects but excludes the
volatile `generation_time`. A repeated run with different generation times is logically and
hash equivalent.

## Diagnostic command

```bash
python collaboration/workstreams/WP-4219/dashboard_cli.py generate \
  --queue collaboration/workstreams/WP-4218/examples/engineering_queue_v1.json \
  --output /tmp/wp4221-output --as-of 1970-01-01T00:00:00Z
python collaboration/workstreams/WP-4219/dashboard_cli.py validate /tmp/wp4221-output/dashboard_snapshot_v1.json
python collaboration/workstreams/WP-4219/dashboard_cli.py explain /tmp/wp4221-output/dashboard_snapshot_v1.json
python collaboration/workstreams/WP-4219/dashboard_cli.py compare LEFT.json RIGHT.json
```

Generation writes only to a new, explicit, non-overlapping output directory. The command has
no discovery, network, subprocess, Git, lifecycle, scheduling, dispatch, assignment, merge,
browser, or installation behavior. Input/output or overlapping paths fail closed.

## Failure, operator use, rollback, and future UI

Operators read campaign health, freshness, ready/blocked work, parallel and merge warnings,
validation gaps, provider degradation, and attention text; corrections occur only in the
governing provider followed by a new WP-4220 publication. A fatal primary queue yields no
snapshot. Optional-provider loss leaves a degraded but renderable snapshot.

Rollback/removal deletes this directory and the WP-4221 package; there is no migration or
production state. A separately authorized install package must select an existing Office or
operator surface, define access/security/accessibility/performance, publication storage,
provider adapters, compatibility, migration, rollback, and acceptance, and prove that it
does not create a second queue or action authority. WP-4219 is not production-installed.
