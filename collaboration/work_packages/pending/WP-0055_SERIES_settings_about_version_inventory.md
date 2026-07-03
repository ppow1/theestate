# SERIES TASK WP-0055 — Settings, About, and Version Inventory

## Codex Command
Read `collaboration/work_packages/pending/WP-0055_SERIES_settings_about_version_inventory.md` and do exactly what it says.

## Mission
Add the first Settings and About surfaces to the Estate Operations Center so UI behavior, visibility preferences, and component versions have a clear home.

## Scope
Create Settings and About views for the Office of the Steward / Estate Operations Center.

Settings should support initial placeholders or working controls for:

- theme: light/dark/system where practical
- refresh behavior
- visible panels
- tab order or pinned views where practical
- global verbosity
- per-topic verbosity placeholders
- per-resident verbosity placeholders
- activity console visibility

About should display a version/component inventory where available:

- Estate version
- Operations Center UI version
- Alfred version/status where available
- Helen version/status where available
- registry/schema versions where available
- Communication Bus version where available
- Work Package schema/version where available
- local runtime paths used by the UI

## Behavior Requirements
- Settings may begin as local UI preferences if no persistent settings store exists.
- Missing component versions should display as unknown/unavailable, not fail.
- Respect UI principles from WP-0046.
- Keep this local-first and simple.

## Constraints
Do not create final user account/authentication policy. Do not store secrets. Do not create cloud settings. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify Settings view renders, About view renders, unknown versions are handled gracefully, and UI preferences do not break the dashboard.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0055_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
