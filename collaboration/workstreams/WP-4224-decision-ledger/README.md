# WP-4224 Recommendation Review and Decision Ledger

This staged package captures the published output of WP-4223 and appends advisory Steward review decisions. It does not generate recommendations, execute work, mutate provider inputs, or confer approval authority.

## Preflight

The local base is merge commit `ac8af06`, containing merged WP-4220 (#474), WP-4221 (#475), WP-4222 (#476), and WP-4223 (#478). No remote is configured in this checkout, so synchronization was reconciled against the provided merged local base. Capability search found recommendation generation in WP-4223 and unrelated decision-support surfaces, but no equivalent immutable recommendation review ledger. Classification before this change: `not_started`; WP-4223 is reused as the sole recommendation source.

## API

`create_ledger(published, generated_at=...)` deterministically captures published recommendations. `append_decision(...)` returns a new value with chained decision and audit records. It never mutates its argument. `query(...)` provides current, historical, history, lineage, superseded, trends, decisions, unresolved, and expired read models. `validate_ledger(...)` verifies versions, hashes, uniqueness, and chains.

Timestamps are supplied by the caller rather than read from the clock, preserving deterministic replay. If omitted during initial capture, the explicit sentinel `unspecified` is recorded.

## CLI

```bash
python ledger_cli.py LEDGER recommendations
python ledger_cli.py LEDGER history [RECOMMENDATION_ID]
python ledger_cli.py LEDGER show RECOMMENDATION_ID
python ledger_cli.py LEDGER compare LEFT RIGHT
python ledger_cli.py LEDGER lineage [RECOMMENDATION_ID]
python ledger_cli.py LEDGER validate
python ledger_cli.py LEDGER explain RECOMMENDATION_ID
```

Every CLI operation reads an existing ledger and writes JSON only to stdout. Decision creation is deliberately library-only so the diagnostic surface cannot modify ledger files.

## Boundaries

The package has no queue, Parking Lot, WIP, work-package, Git, scheduler, dispatcher, worker, merge, or execution adapter. `accepted_for_future_planning` and `rejected` describe advisory disposition only; neither approves nor rejects implementation.
