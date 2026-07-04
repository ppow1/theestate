# SERIES TASK WP-0093 — Operations Center Settings Manager

## Codex Command
Read `collaboration/work_packages/pending/WP-0093_SERIES_operations_center_settings_manager.md` and do exactly what it says.

## Mission
Implement the Operations Center Settings Manager so Steward-facing UI preferences, workspace defaults, refresh behavior, appearance settings, and operator visibility controls are managed in one local, version-aware place.

## Scope
Build on the Operations Center Layout Framework, Workspace Profiles, Operator Verbosity and Filter Profiles, Command Console, and Help/About surfaces.

The Settings Manager should support:

- light/dark appearance preference
- accent or theme setting if an existing UI convention supports it
- default workspace profile
- default panel visibility
- status bar and bottom activity stream preferences
- default verbosity profile
- refresh interval / quiet refresh behavior
- command console preferences where appropriate
- settings version metadata
- local-first persistence
- safe defaults when settings are missing or invalid

## Behavior Requirements
- Use existing UI/configuration infrastructure where available.
- Do not scatter settings across unrelated components.
- Missing settings should fall back to documented defaults.
- Invalid settings should fail safely and be reported clearly.
- Settings should be version-aware so future migrations are possible.
- Settings should integrate with Help/About so the current UI/config version can be inspected.

## Constraints
Do not create a cloud settings dependency. Do not store secrets. Do not override governance or authority controls. Do not duplicate an existing settings system if one already exists. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify default settings, persistence, invalid-setting handling, missing-file handling, version metadata, appearance preference, workspace default selection, verbosity default selection, and compatibility with existing Operations Center components.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0093_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
