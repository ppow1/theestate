# WP-0214 Left Navigation Layout Report

## What changed

- The Office shell no longer reserves a persistent left navigation column.
- The main Office layout now uses a single full-width workspace grid by default.
- The former left navigation is retained as a collapsed-by-default overlay drawer, opened from the compact `Office Navigation` summary/toggle.
- Selecting a destination from the drawer activates the corresponding top-tab workspace and closes the drawer.
- The layout framework now declares the default left navigation state as collapsed.
- Workspace profiles now default `left_navigation` to `collapsed`.
- Legacy profile state that says `left_navigation: expanded` is interpreted safely as `collapsed` and emits a compatibility warning instead of expanding the Office by default.

## Removed or collapsed

Chosen implementation: `collapsed_by_default`.

The side navigation was not removed completely because it still provides a compact secondary index for keyboard/mouse users and older tests expect an Office navigation region. It no longer permanently consumes viewport width.

## Why this approach was used

The top tab system already provides full access to all Office areas and remains the primary workspace controller. Keeping the side navigation as a collapsed overlay preserves secondary access without duplicating a full-size navigation system on screen or shrinking the workspace.

## Files changed

- `src/estate/core/steward_command_center.py`
- `src/estate/core/operations_center_workspace_profiles.py`
- `tests/test_steward_command_center.py`
- `operations/steward/WP-0214_left_navigation_layout_report.md`
- `collaboration/work_packages/completions/WP-0214_codex_done.json`

## How tab access is preserved

The Office payload still exposes all top tabs:

- Home
- Mission Control
- Alfred
- Helen
- Resident Conversations
- AI Services / Models
- Daily Board
- Projects
- Roadmap
- Parking Lot
- Work Packages
- Mailboxes
- Recalls
- Notifications
- Validation
- Search
- Settings
- Help
- About

The rendered top tab bar remains the primary active workspace navigation. Drawer buttons use the same `data-tab` activation path as the top tabs, so every drawer destination targets an existing workspace section.

## How the main viewport gains space

Before WP-0214, `.office-shell` used a two-column grid with a `minmax(13rem,17rem)` left navigation column and the workspace in the second column. After WP-0214, `.office-shell` uses `grid-template-columns:1fr`, and the navigation drawer is fixed-position overlay UI. Closed drawer state therefore does not reserve horizontal layout space.

## Compatibility handling

- New default workspace profiles write `panel_arrangements.left_navigation` as `collapsed`.
- Existing profile artifacts with `panel_arrangements.left_navigation: expanded` are normalized to `collapsed` during profile resolution.
- A `left_navigation_layout_migrated` warning is added when the legacy expanded state is encountered.
- Browser local layout preference restoration normalizes an `expanded` left-navigation value to `collapsed` before applying preferences.
- Operational behavior, command execution, resident behavior, validation behavior, and Estate authority semantics were not changed.

## Tests and validation run

- `PYTHONPATH=src python -m pytest tests/test_steward_command_center.py -q` — passed, 43 tests.
- `PYTHONPATH=src python -m estate.cli.main steward-command-center --json` — succeeded and generated command center JSON/HTML.
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0214 --json` — succeeded with no failures/findings.
- `PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json` — command succeeded; output still reports existing unrelated production-readiness backlog blockers.

## Manual verification steps for the Steward

1. Start the Office locally, for example with the repository's Steward Command Center launch path.
2. Open the Office in the browser.
3. Confirm the left menu is collapsed by default and does not occupy a permanent left column.
4. Confirm the top tabs still change the active viewport.
5. Confirm all Office areas listed above remain reachable from the top tabs.
6. Confirm the main workspace has more horizontal room than before because it spans the single-column Office shell.
7. Open the `Office Navigation` drawer, choose a destination, and confirm the drawer closes after selection.
8. Confirm the drawer is visually distinct from the main content and overlays rather than permanently pushing it aside.

## Known limitations

- This change does not add an animated off-canvas drawer; it uses the native `details` disclosure element styled as a fixed overlay.
- The drawer is intentionally secondary; the top tab bar remains the authoritative workspace navigation.
- `validation-production-readiness --json` still reports unrelated existing backlog blockers outside WP-0214 scope, despite the command completing successfully.
