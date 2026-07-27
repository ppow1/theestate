# WP-4226 — Campaign Snapshot and Replay

## Status and preflight

Classification: **not_started**, then implemented by this work package. The prerequisite
merge commits for WP-4220 through WP-4225 are present in order in the synchronized input
history (`a3f12b2`, `8aa9c0d`, `1b93db5`, `d9e9519`, `6006e37`, `4075e6f`). The checkout
has no configured remote, so synchronization was reconciled against the supplied shallow
`main` history rather than a network remote. Repository search found general runtime/PTM
replay concepts but no campaign snapshot/replay CLI. This implementation reuses the six
published projections and their hashes; it does not duplicate their builders or policies.

## Architecture

`estate.core.engineering_campaign_replay` is a pure value layer. A snapshot accepts exactly
the published WP-4220 queue, WP-4221 dashboard, WP-4222 integration, WP-4223 recommendations,
WP-4224 ledger, and WP-4225 analytics objects. It deep-copies them verbatim and records schema
versions, health, freshness, degradation, provenance, caller-supplied generation time, and a
canonical SHA-256 hash. It never discovers or regenerates source records.

Replay returns captured dashboard, recommendation, analytics, decision, dependency, merge-risk,
and engineering-metric projections. Comparison reports work-set, captured priority/dependency,
analytics, health, and degradation changes. No replay path imports schedulers, dispatchers,
workers, Git adapters, recommendation policy, or analytics policy.

Schemas and nine representative fixtures are under `schemas/` and `fixtures/`.

## Commands

Run from the repository root with `PYTHONPATH=src python -m estate.cli.engineering_campaign_replay`:

* `snapshot SOURCES --generated-at TIMESTAMP` — emit a snapshot from one six-key JSON bundle.
* `replay SNAPSHOT` — emit the replay manifest and captured views.
* `compare LEFT RIGHT` — report captured differences.
* `history SNAPSHOT...` / `list SNAPSHOT...` — list stable chronological metadata.
* `validate SNAPSHOT` — validate version, boundary, hash, and provenance.
* `explain SNAPSHOT` — explain versions and source provenance.

All output is written to stdout. The CLI has no output-file option and opens input paths only
for reading; shell redirection, if desired, remains an explicit caller action.
