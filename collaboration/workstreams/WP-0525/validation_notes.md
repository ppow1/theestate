# WP-0525 Validation Notes

## Validation Coverage
The staged tests prove:

- truthful presence cards preserve only supplied active assignment, completion, blocker, and evidence values;
- stale-data handling computes freshness from timestamps and marks attention required;
- drill-down links open assignments, conversations, mailboxes, and work packages, while missing links are reported honestly;
- filtering works by resident, office, status, and attention state;
- missing evidence is visible and is not filled with fake activity;
- blocker state takes precedence over generic attention state;
- guardrails explicitly reject fabricated activity, hidden monitoring, and authority expansion.

## Command
`python -m pytest collaboration/workstreams/WP-0525/staged/test_office_resident_presence.py`

## Staging Statement
This work is staged under `collaboration/workstreams/WP-0525/` only. It is not installed work. Shared active Office files were not modified.
