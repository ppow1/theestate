# WP-4053 Dynamic Resident Preference and Personality Evolution

This staged package implements a source-linked resident preference layer in isolation under `collaboration/workstreams/WP-4053/`. It does **not** install code into active runtime paths.

## Artifacts

- `src/wp4053_preferences/engine.py` — deterministic staged preference engine.
- `schemas/preference_record_v1.json` — versioned preference record contract.
- `schemas/preference_change_proposal_v1.json` — resident proposal/review contract.
- `fixtures/*_preferences.json` — deterministic Grace, Ingrid, and Evelyn fixtures.
- `tests/test_preference_engine.py` — acceptance and boundary tests.
- `docs/integration_notes.md` — installation touchpoints and privacy boundaries.
- `docs/rollback_notes.md` — rollback plan.

## Rules implemented

The engine records observations without automatic promotion, reinforces evidence, detects contradictions, promotes only with approved authority, supports experimentation, preserves lineage on change, scopes context keys, retires/forgets records with minimum audit metadata, keys by resident ID, and blocks ordinary model output from durable identity changes.
