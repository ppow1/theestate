# SERIES TASK WP-0093 — Operations Center Settings Manager

## Codex Command
Read `collaboration/work_packages/pending/WP-0093_SERIES_operations_center_settings_manager.md` and do exactly what it says.

## Mode

SERIES

## Mission
Implement the Operations Center Settings Manager so Steward-facing UI preferences, workspace defaults, refresh behavior, appearance settings, and operator visibility controls are managed in one local, version-aware place.

## Background

This work package remains a pending backlog item. WP-0102 added this background section to align the file with the Codex Task Template Standard while preserving the original mission and scope.

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


## WP-0102 Template Retrofit Notice

This section was added by WP-0102 as a mechanical template retrofit. It preserves the original mission and scope above. This pending package remains authored and queued; it is not implemented, validated, operationally validated, approved, or institutionalized by this retrofit.

## Out of Scope

- Do not change the original mission or core scope of WP-0093.
- Do not treat this pending package as already implemented or validated.
- Do not modify `estate_ledger/ledger.md` or `development/devlog.md` unless a future package explicitly authorizes it.
- Do not change governance authority, validation authority, merge authority, or automatic approval behavior.

## Required Behavior

- Execute the original package behavior described above when this package is later implemented.
- Preserve local-first operation unless the Steward explicitly authorizes networked behavior.
- Leave auditable evidence for every check, limitation, and generated artifact.
- Report known limitations explicitly instead of implying production readiness.

## Safety and Authority Constraints

- Do not change governance authority.
- Do not change validation authority.
- Do not automatically approve work packages.
- Do not modify `estate_ledger/ledger.md`.
- Do not modify `development/devlog.md`.
- Do not weaken Git safety behavior.
- Do not stage broad paths.
- Preserve local-first operation unless explicitly authorized.

## Required CLI / Command Surface

Use the command surfaces already named in this package. If implementation changes introduce or alter CLI behavior, document exact command names and acceptable local-first alternatives in the completion receipt.

## Required Artifacts

- Implement the artifacts already specified by this pending package.
- Create `collaboration/work_packages/completions/WP-0093_codex_done.json`.
- Add or update the registered validation recipe for `WP-0093` unless this file explicitly states that the recipe is not applicable.

## Validation Recipe Requirement

Add or update the validation recipe for WP-0093. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure future validation can evaluate this package with:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0093 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement

Create `collaboration/work_packages/completions/WP-0093_codex_done.json` with at least:

- `work_package_id`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- `files_changed`
- `tests_run`
- `known_limitations`
- `ready_for_ca_review`
- `merge_authority`
- validation recipe status or not-applicable rationale
- production readiness command status if run
- final command surfaces or Steward commands when applicable

Missing receipt metadata blocks production-readiness status under the WP-0095 validation standard.

## Production Readiness Requirement

This package must remain compatible with the production-readiness validation loop. When practical, run or document the equivalent of:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0093 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If readiness remains blocked by intentionally pending work, missing external dependencies, or a documented recipe exception, record that limitation in the completion receipt rather than claiming readiness.

## Demonstration Requirements

Document the exact commands run and observed status in the completion receipt. Include evidence for implementation-time checks, validation recipe behavior where applicable, and production-readiness compatibility.

## Merge Class
Class A.
