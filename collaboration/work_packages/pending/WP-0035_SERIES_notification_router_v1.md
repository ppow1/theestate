# SERIES TASK WP-0035 — Notification Router v1

## Codex Command
Read `collaboration/work_packages/pending/WP-0035_SERIES_notification_router_v1.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0033 Autonomous Estate Operations Charter and WP-0034 Steward Recall Decision Model.

## Mission
Implement Notification Router v1 as a transport-independent routing layer for recall-worthy Estate events.

## Why This Is Next
The Estate needs Steward Recall, but recall must not be tied directly to Gotify or any single transport. The router decides what notification event should be emitted; adapters deliver it.

## Scope
Create a bounded notification router module such as:

- `src/estate/core/notification_router.py`

The router should accept structured inputs from existing or simulated sources:

- Communication Bus events
- Operations Board events
- Audit/validation events
- worker events
- Alfred recall decisions

For v1, the router should produce only two classes:

- recall
- informational

Only recall events should be eligible for immediate transport delivery. Informational events should be deferred to morning briefing or reports.

## Expected Outputs
- Notification router module.
- Runtime output such as `runtime/notifications/notification_router_report.json`.
- Optional CLI if consistent with existing patterns, for example:

```bash
PYTHONPATH=src python -m estate.cli.main notification-router --json
```

## Behavior Requirements
- Router must not know about Gotify implementation details.
- Router must include reason, requested_by, priority, action, and audit fields.
- Missing optional inputs should warn, not fail.
- Successful routine events must not produce recall output.

## Tests
Add tests for:

- constitutional recall event routes as recall
- architectural decision request routes as recall when policy indicates it
- successful Codex run routes as informational
- normal mailbox update routes as informational
- router output does not contain Gotify-specific fields

## Constraints
Do not implement Gotify adapter in this package. Do not contact external services. Do not bypass Alfred. Do not give workers authority to notify the Steward directly. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0035_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded routing implementation after CA verification. Escalate to Class B only if implementation changes recall authority or creates direct worker-to-Steward notification paths.
