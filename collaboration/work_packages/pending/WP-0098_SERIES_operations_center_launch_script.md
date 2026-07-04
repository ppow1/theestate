# SERIES TASK WP-0098 — Operations Center Launch Script

## Codex Command
Read `collaboration/work_packages/pending/WP-0098_SERIES_operations_center_launch_script.md` and do exactly what it says.

## Mission
Create the Steward-facing local launch script for the Estate Operations Center so the control-room interface can be started from the Estate workspace with one clear operator action.

## Scope
Build on the Operations Center Local Server Bootstrap, Settings Manager, Status Bar, Notification Center, Command Console, and existing local CLI conventions.

The launch path should provide a simple local entry point such as a PowerShell script, CLI wrapper, or existing repo-native command that can:

- verify the Estate root
- check required local dependencies
- load local configuration/settings
- start the Operations Center local server
- print the local URL
- report degraded or unavailable optional components
- preserve clear operator instructions
- support safe shutdown guidance

## Behavior Requirements
- Local-first only.
- No cloud dependency.
- No secret storage.
- No automatic work package execution.
- No authority bypass.
- Clear failure messages.
- Compatible with existing Windows/PowerShell operator workflow where possible.
- Respect existing repository conventions rather than introducing unrelated launcher patterns.

## Constraints
Do not create a second Operations Center implementation. Do not bypass the local server bootstrap. Do not create a new governance or command authority path. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify launch from the Estate root, missing dependency handling, configuration loading, server startup reporting, URL display, degraded optional component reporting, and safe failure behavior.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0098_codex_done.json` using the standard completion schema.

## Merge Class
Class A unless command authority, runtime execution, or governance semantics are changed; escalate to Class B if those boundaries are altered.
