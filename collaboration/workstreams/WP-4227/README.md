# WP-4227 Recommendation Confidence and Evidence Framework

This read-only framework assesses evidence attached to **published** WP-4220 through
WP-4226 outputs. It never regenerates an upstream artifact and never changes a
recommendation, its score/order, Git, lifecycle state, scheduling, dispatch, or
assignment state. The preflight classified prior capability as `not_started`;
WP-4226 canonical hashing, provenance, comparison, history, and read-only CLI
patterns were reused rather than duplicated conceptually.

## Deterministic method

Each recommendation receives eight Boolean checks: provenance, dependencies,
validation, merge risk, freshness, provider availability, referenced data, and
supported schema. The count maps to `very_high` (8), `high` (6–7), `moderate`
(5), `low` (3–4), or `insufficient_evidence` (0–2). Any conflicting evidence
forces `low`. Canonical, sorted JSON plus a trailing newline is SHA-256 hashed.
No probability, model inference, wall clock, filesystem discovery, or network
state participates. `--assessed-at` is explicit so replay is reproducible.

Inputs must contain exactly the six published sources represented by WP-4226's
snapshot contract: queue, dashboard, integration, recommendations, decision
ledger, and analytics. Unsupported schemas and malformed records fail closed.

## CLI

Run with `PYTHONPATH=src python -m estate.cli.engineering_recommendation_confidence`:

* `confidence SOURCES --assessed-at TIMESTAMP`
* `evidence SOURCES --assessed-at TIMESTAMP`
* `explain REPORT RECOMMENDATION_ID`
* `compare LEFT RIGHT`
* `validate REPORT`
* `history REPORT [REPORT ...]`

All commands write JSON to stdout only. Schemas are in `schemas/`; all eight
required scenarios are in `fixtures/`.
