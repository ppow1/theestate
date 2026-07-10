# WP-0526 Workspace Personalization Contract

This contract stages Office workspace personalization only. It is not installed work and must be installed by WP-0531 before any shared active Office files consume it.

## Schema

Personalization documents use `estate.office_workspace_personalization.v1` and include:

- `workspace_id`: workspace/profile identifier.
- `active_layout_id`: selected saved layout.
- `saved_layouts`: map of layout id to visible sections, section order, and preferences.
- `pins`: ordered pinned `project`, `work_package`, `resident`, and `artifact` identifiers.
- `favorite_residents`: ordered resident identifiers.
- `quick_actions`: ordered favorite action identifiers for quick launch.
- `staged_not_installed`: always `true` while staged.
- `recovered_from_malformed_state` and `recovery_notes`: visible recovery metadata.

## Required Behavior

- Save layouts without mutating the supplied state object.
- Preserve pinned projects, work packages, residents, and artifacts in user-selected order.
- Preserve favorite residents and quick-launch actions in user-selected order.
- Support per-workspace visibility, section ordering, and preferences.
- Restore defaults from `WorkspaceDefaults`.
- Recover malformed, missing, unsupported-schema, or invalid JSON state to safe defaults with visible recovery notes.
- Import/export only safe structured JSON.

## Deferred Installation Hooks

WP-0531 should connect the staged module to settings/profile storage, Office rendering, quick-launch controls, pin buttons, favorite resident controls, and restore/import/export UI surfaces.

## Declared Conflict Surface

This work overlaps with WP-0511 Settings and workspace profiles, future settings schema migrations, and Office rendering hooks. Installation must reconcile ownership of workspace profile persistence before activation.
