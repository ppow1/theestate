# WP-0525 - Resident Presence and Operational Activity

## Codex Command
Read collaboration/work_packages/pending/WP-0525_PARALLEL_STAGED_Resident_Presence_and_Operational_Activity.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Build a staged resident-presence and activity surface that truthfully shows what residents and operational roles are doing, what they completed, what is blocked, and where supporting evidence lives.

## Required Capabilities
- current presence and duty state;
- active assignment, last completed duty, blocker, and attention requirement;
- drill-down to assignments, conversations, mailboxes, work packages, and evidence;
- freshness and stale-state indicators;
- no fabricated activity, hidden monitoring, or authority expansion;
- filter by resident, office, status, and attention state.

## Staging Requirements
Create under `collaboration/workstreams/WP-0525/`:

```text
install_manifest.json
staged/office_resident_presence.py
staged/test_office_resident_presence.py
resident_presence_contract.md
validation_notes.md
rollback_notes.md
```

Do not modify shared active Office files. WP-0531 performs installation.

## Conflict Surface
Expected final targets include a dedicated presence module, Office workspace registration, links into existing resident artifacts, tests, and docs. Declare overlaps with existing `steward_presence`, resident cards, and activity modules.

## Validation
Prove truthful presence, stale-data handling, drill-down links, filtering, missing evidence, and no fabricated activity.

## Completion Receipt
Create `collaboration/work_packages/completions/WP-0525_codex_done.json` and state that staged work is not installed work.
