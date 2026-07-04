# SERIES TASK WP-0097 — Operations Center Local Server Bootstrap

## Codex Command
Read `collaboration/work_packages/pending/WP-0097_SERIES_operations_center_local_server_bootstrap.md` and do exactly what it says.

## Mission
Create the first local server bootstrap path for the Estate Operations Center so the Steward can launch the control-room interface from the local Estate runtime without relying on cloud services or manual file browsing.

## Scope
Build on the Operations Center Layout Framework, Workspace Profiles, Settings Manager, Status Bar, Notification Center, Service Health Registry, Operator Activity Stream, and Command Console.

The bootstrap should provide a safe local entry point for starting, inspecting, and stopping the Operations Center server using existing repository conventions.

Possible commands may include, if consistent with existing patterns:

- `estate operations-center start`
- `estate operations-center status`
- `estate operations-center stop`
- `estate ops start`

Follow existing CLI conventions rather than inventing unrelated command names.

The implementation should expose or document:

- local host/port behavior
- startup checks
- static or app entry point
- configuration loading
- settings loading
- service health preflight
- safe failure when dependencies are missing
- clear operator instructions

## Behavior Requirements
- Local-first only.
- Do not require internet access.
- Do not require external identity providers.
- Do not store secrets.
- Missing optional dashboards or widgets should degrade gracefully.
- Startup should report what is available, degraded, or unavailable.
- The server should not execute work packages automatically.
- The server should not bypass command authority, Steward authorization, or recall semantics.

## Constraints
Do not introduce a cloud dashboard. Do not create a second Operations Center implementation if one already exists. Do not bypass existing CLI patterns. Do not create a new authority model. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify local startup, local status inspection, graceful missing-dependency handling, settings loading, unavailable optional component handling, safe shutdown if implemented, and clear operator-facing output.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0097_codex_done.json` using the standard completion schema.

## Merge Class
Class A unless runtime authority, command execution semantics, or governance boundaries are changed; escalate to Class B if those semantics are altered.
