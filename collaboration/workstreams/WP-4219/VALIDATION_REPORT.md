# WP-4221 staged validation report

- **Date:** 2026-07-26
- **Result:** pass
- **Environment:** offline checkout; CPython 3; pytest
- **Focused fixtures:** 18 named synthetic queue scenarios; no live repository state
- **Panels:** 15/15 common versioned read models
- **Snapshot SHA-256:** `81f5e1b14cb64dd2eaf85c7fc02dd22072c7c788ffcf42bbcc16ffd6ab4db906`
- **Logical snapshot ID:** `d323ffa95b1e6cff3c5f`

`pytest -q collaboration/workstreams/WP-4218/tests/test_reconciler.py
collaboration/workstreams/WP-4219/tests/test_dashboard.py` passed 18 tests. It covers the
WP-4220 consumer contract, all panels, schema invariants, executive totals, ready/blocked
filters, graph cycles/missing dependencies, parallel and merge-risk views, metric unavailable
states, provider degradation, freshness, empty versus unavailable, provenance, stable order,
hashing, repeated runs, malformed/version/duplicate failure, source preservation, explicit
output boundaries, and CLI success/degraded/fatal/compare behavior.

Two runs with reversed input traversal and different volatile generation timestamps produced
the same logical ID and deterministic content hash. A separate CLI two-run comparison also
reported `equivalent`. Optional duration, Git, activity, audit, capacity, and historical facts
were validated as unavailable/partial while the snapshot remained renderable. Invalid primary
queues produced no output directory. The WP-4220 suite continued to pass.

Changed-path inspection found only the WP-4221 governing package plus files beneath the
WP-4219 staging root. No prohibited HTML/CSS/JavaScript/TypeScript or production/shared path
was added. JSON Schema documents were syntax checked and are exercised by equivalent internal
invariants; the optional `jsonschema` Python package was unavailable in this environment.

Known limitations: WP-4220 v1 carries references rather than duration values, Git observation
details, lane capacity, activity/audit streams, validation recipe detail, promotion timestamps,
or critical-path results. The projection therefore cannot truthfully calculate those values.
No production publisher, prior-snapshot audit store, UI, or installation exists.
