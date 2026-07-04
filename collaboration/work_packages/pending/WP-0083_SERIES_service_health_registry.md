# SERIES TASK WP-0083 — Service Health Registry

## Codex Command
Read `collaboration/work_packages/pending/WP-0083_SERIES_service_health_registry.md` and do exactly what it says.

## Mission
Create a Service Health Registry that aggregates operational health information for Estate services, providing a common read-only view for Mission Control, the Operations Center, and Alfred.

## Scope
Build on the Estate Service Catalog and Service Dependency Matrix to expose service status, availability, health indicators, validation state, dependency health, and last-known update information.

## Behavior Requirements
- Read-only aggregation.
- Do not become the source of truth.
- Link every health entry to its authoritative source.
- Support future dashboard widgets and alerts.
- Handle unavailable services gracefully.

## Constraints
Do not duplicate monitoring systems. Do not fabricate health data. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify healthy, degraded, unavailable, unknown, and missing-metadata states. Verify source-link integrity.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0083_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
