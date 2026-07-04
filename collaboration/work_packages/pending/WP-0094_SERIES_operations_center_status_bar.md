# SERIES TASK WP-0094 — Operations Center Status Bar

## Codex Command
Read `collaboration/work_packages/pending/WP-0094_SERIES_operations_center_status_bar.md` and do exactly what it says.

## Mission
Implement the Operations Center Status Bar as the persistent bottom-line operational surface for quick Estate state awareness and access to key controls.

## Scope
Build on the Operations Center Layout Framework, Service Health Registry, Operator Activity Stream, Command Console, Workspace Profiles, and Settings Manager.

The status bar should display concise indicators for:

- overall Estate readiness
- service health
- validation status
- active worker/runtime status
- notification/recall state
- current workspace profile
- activity stream state
- command console access
- current settings/profile state where appropriate

## Behavior Requirements
- Persistent but unobtrusive.
- Quiet updates without page blinking.
- Compact indicators with drill-down affordances.
- Support enabling/disabling optional activity strip controls.
- Respect settings and verbosity preferences.
- Degrade gracefully when upstream data is unavailable.

## Constraints
Do not become the source of truth for operational state. Do not duplicate service health or validation data. Do not bypass command authority through status bar controls. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering with healthy, degraded, blocked, missing-data, and offline states. Verify command-console access, activity-stream toggle behavior, source links, and settings integration.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0094_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
