# Multi-Repository Operational Targets

WP-0631 generalizes Background Operations and post-merge validation so the Estate runtime can observe multiple governed repositories without duplicating orchestrators, event buses, schedulers, or audit systems.

## Target model

`MultiRepositoryOperationalTarget` records the repository URL/path, base branch, workspace root, evidence root, enabled capabilities, watch profile, validation binding, department owner, aliases, and mode. Modes are:

- `enabled`: discovery and audits may run through the existing governed surfaces.
- `observe_only`: read-only observation is allowed, but audits are not enabled.
- `disabled`: the target is retained in the registry but skipped by cycles.

Estate and Cue Mastery are registered by default. Cue Mastery starts in `observe_only` mode so it can be monitored before audits are enabled.

## State isolation

The runtime scopes mutable artifacts by `target_id`:

- cursors: `runtime/merge_discovery/targets/<target_id>`
- workspaces: `<workspace_root>/<target_id>`
- evidence: `<evidence_root>/<target_id>`
- holds: `runtime/operational_targets/holds/<target_id>`
- verdicts: `runtime/post_merge_audit/verdicts/by_target/<target_id>`

This prevents Estate and Cue Mastery from colliding while still reusing the existing discovery, cleanroom/audit, scheduler, and Office-facing concepts.

## Validation bindings

Targets do not need to use Estate work-package numbering. The `validation_binding` field describes how validation should be invoked for that repository. Estate uses an `estate_work_package` binding; Cue Mastery starts with an external binding that can be replaced when its native validation recipe is governed.

## Failure isolation and Office grouping

`MultiRepositoryOperationalRuntime.run_cycle()` invokes a caller-provided handler per active target and records failures per target without stopping subsequent targets. `office_status()` groups repository activity by `department_owner` and includes each repository's isolated state paths for Office display.
