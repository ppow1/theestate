# Engineering Campaign Dashboard operator surface

## Decision and authority

The canonical installation target is the existing **Office of the Steward local command
center**, already established as the Estate operator workspace with local routing, quiet
refresh, settings, diagnostics, and audit integrations. WP-4219 expressly requires a later
install package to select an existing operator surface; WP-4222 supplies that install handoff.
WP-4223 adds one tab and does not create a shell, gateway, API framework, or UI framework.

## Source flow and contract

`WP-4220 queue → WP-4221 projection → WP-4222 registry/composition → WP-4223 Office adapter`.
The adapter loads only the configured WP-4222 manifest. It never discovers work packages,
reconciles queue state, or interprets lifecycle records. The Office tab renders all 15 panels,
including the dependency graph as deterministic structured JSON. Empty, unavailable, stale,
unsupported, partially degraded, and healthy states remain explicit.

Read-only served-mode routes are:

- `GET /api/engineering-dashboard/snapshot`
- `GET /api/engineering-dashboard/panel?panel=<panel-id>`
- `GET /api/engineering-dashboard/summary`
- `GET /api/engineering-dashboard/health`
- `GET /api/engineering-dashboard/compatibility`
- `GET /api/engineering-dashboard/diagnostics`
- `GET /api/engineering-dashboard/refresh`

Each requires `X-Estate-Operator-Role: estate_operator` or `steward`. Refresh means recomposing
approved immutable providers; it does not alter them. No write verb or mutating control exists.

## Configuration and workflow

`config/engineering_campaign_dashboard.json` controls enablement, manifest location, manual
refresh policy, freshness threshold, last-known-valid behavior, safe diagnostic verbosity,
and allowed operator roles. Operators open **Engineering Dashboard**, review health/freshness,
summary and panels, inspect provider diagnostics/provenance, and select **Manual refresh**.
Existing Office automatic refresh is not extended to provider recomposition.

Every valid response includes queue generation ID, source revision, snapshot ID, schema,
generation time, freshness, provider availability/degradation, source references, and hashes.
Optional-provider failures preserve valid primary data. Required-provider failure cannot appear
healthy. A failed refresh identifies the current source as unavailable and, when configured,
labels the retained snapshot as last-known-valid rather than current.

Audit records contain access/refresh outcome metadata, revision/snapshot identifiers, and safe
diagnostics only. Raw provider content, credentials, tokens, secrets, and unrestricted paths are
not logged or exposed by the adapter.

## Rollback

1. Set `enabled` to `false` in `config/engineering_campaign_dashboard.json`.
2. Regenerate/restart the Office command center.
3. Confirm the tab reports `unsupported: dashboard_disabled` and other Office tabs operate.
4. Optionally delete only `runtime/steward/engineering_campaign_dashboard_last_valid.json` and
   `runtime/audit/engineering_campaign_dashboard.jsonl` under normal retention policy.

Do not remove or modify WP-4220, WP-4221, WP-4222, their provider artifacts, authoritative queue
records, Parking Lot, WIP, or Git history. Future work may replace the configured staged manifest
with a governed published manifest; it may not add scheduling or mutation authority.
