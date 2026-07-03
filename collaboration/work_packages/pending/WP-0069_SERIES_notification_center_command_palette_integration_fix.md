# SERIES TASK WP-0069 — Notification Center Command Palette Integration Fix

## Codex Command
Read `collaboration/work_packages/pending/WP-0069_SERIES_notification_center_command_palette_integration_fix.md` and do exactly what it says.

## Mission
Resolve the WP-0056 validation follow-up identified by Chief Architect #4: the Notification Center Workspace is discoverable through Global Search but is not registered or reachable through the Command Palette.

## Validation Context
Chief Architect #4 reported:

- WP-0056 should not be marked fully validated yet.
- Notification Center Workspace is discoverable via Global Search.
- `palette-command notification-center` returns unavailable.
- This indicates a missing integration point rather than a workspace crash.

Treat this as an integration correction, not a redesign of WP-0056.

## Scope
Investigate and correct the Command Palette registration path for the Notification Center Workspace.

Verify:

- whether WP-0056 explicitly required Command Palette registration
- whether Operations Center workspace convention requires palette registration
- where command registrations currently live
- whether `notification-center` or an equivalent command alias should be registered
- whether Global Search and Command Palette use separate registries or shared command metadata

Implement the smallest safe correction so the Notification Center can be opened from the Command Palette.

## Expected Behavior
After implementation, a Steward/operator should be able to invoke the Notification Center from the Command Palette using an obvious command such as:

- `notification-center`
- `open notification center`
- or the existing local convention for workspace commands

The exact command names should follow existing repository patterns.

## Constraints
Do not redesign the Notification Center Workspace. Do not rewrite Global Search. Do not create a new command system if one already exists. Do not create new governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify:

- Notification Center remains discoverable through Global Search.
- Notification Center is reachable through the Command Palette.
- Existing Command Palette commands still work.
- Missing or unavailable commands still produce clear unavailable responses.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0069_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
