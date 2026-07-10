# WP-0528 - Estate Timeline and Operational History

## Codex Command
Read collaboration/work_packages/pending/WP-0528_PARALLEL_STAGED_Estate_Timeline_and_Operational_History.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Build a staged unified operational timeline over existing merges, validations, decisions, resident duties, Office actions, provider results, and operational events.

## Required Capabilities
- normalized chronological entries with source type and evidence path;
- filters by date, actor, package, project, office, event type, and outcome;
- drill-down to canonical artifacts;
- correlation of related events without rewriting source history;
- freshness, gap, duplicate, and malformed-evidence indicators;
- export of filtered history;
- no new authority or competing event source.

## Staging Requirements
Create under `collaboration/workstreams/WP-0528/`:

```text
install_manifest.json
staged/office_operational_timeline.py
staged/test_office_operational_timeline.py
operational_timeline_contract.md
validation_notes.md
rollback_notes.md
```

Do not modify shared active Office files. WP-0531 performs installation.

## Conflict Surface
Expected final targets include a dedicated timeline module, Office workspace registration, adapters over existing evidence sources, tests, and docs. Declare overlap with operational activity and event-subscription work.

## Validation
Prove deterministic ordering, correlation, filtering, source links, duplicate suppression, malformed evidence handling, and export.

## Completion Receipt
Create `collaboration/work_packages/completions/WP-0528_codex_done.json` and state that staged work is not installed work.
