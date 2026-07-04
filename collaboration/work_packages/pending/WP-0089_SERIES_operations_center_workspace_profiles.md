# SERIES TASK WP-0089 — Operations Center Workspace Profiles

## Codex Command
Read `collaboration/work_packages/pending/WP-0089_SERIES_operations_center_workspace_profiles.md` and do exactly what it says.

## Mission
Implement configurable Operations Center workspace profiles that allow the Steward to switch between task-focused layouts such as Mission Control, Validation, Expansion Planning, Active Projects, and Administration.

## Scope
Build on the Operations Center Layout Framework by supporting named workspace profiles, default panel arrangements, tab selections, visibility settings, and future user-customized layouts.

## Behavior Requirements
- Persist workspace configurations.
- Support rapid profile switching.
- Integrate with operator verbosity and filter profiles.
- Preserve version information and layout compatibility.
- Use existing UI state infrastructure where available.

## Constraints
Do not duplicate UI configuration systems. Do not implement visual themes beyond existing settings. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify profile save/load, layout restoration, compatibility across versions, and graceful handling of unavailable panels.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0089_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
