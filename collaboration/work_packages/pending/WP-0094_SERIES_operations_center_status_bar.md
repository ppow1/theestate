# SERIES TASK WP-0094 — Operations Center Status Bar

## Codex Command
Read `collaboration/work_packages/pending/WP-0094_SERIES_operations_center_status_bar.md` and do exactly what it says.

## Mode

SERIES

## Mission
Implement the Operations Center Status Bar as the persistent bottom-line operational surface for quick Estate state awareness and access to key controls.

## Background

This work package remains a pending backlog item. WP-0102 added this background section to align the file with the Codex Task Template Standard while preserving the original mission and scope.

## Scope
Build on the Operations Center Layout Framework, Service Health Registry, Operator Activity Stream, Command Console, Workspace Profiles, and Settings Manager.

The status bar should display concise indicators for:

- overall Estate readiness
- service health
- validation status
- active worker/runtime status
- notification/recall state
- current workspace profile
- activity stream state
- command console access
- current settings/profile state where appropriate

## Behavior Requirements
- Persistent but unobtrusive.
- Quiet updates without page blinking.
- Compact indicators with drill-down affordances.
- Support enabling/disabling optional activity strip controls.
- Respect settings and verbosity preferences.
- Degrade gracefully when upstream data is unavailable.

## Constraints
Do not become the source of truth for operational state. Do not duplicate service health or validation data. Do not bypass command authority through status bar controls. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering with healthy, degraded, blocked, missing-data, and offline states. Verify command-console access, activity-stream toggle behavior, source links, and settings integration.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0094_codex_done.json` using the standard completion schema.


## WP-0102 Template Retrofit Notice

This section was added by WP-0102 as a mechanical template retrofit. It preserves the original mission and scope above. This pending package remains authored and queued; it is not implemented, validated, operationally validated, approved, or institutionalized by this retrofit.

## Out of Scope

- Do not change the original mission or core scope of WP-0094.
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
- Create `collaboration/work_packages/completions/WP-0094_codex_done.json`.
- Add or update the registered validation recipe for `WP-0094` unless this file explicitly states that the recipe is not applicable.

## Validation Recipe Requirement

Add or update the validation recipe for WP-0094. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure future validation can evaluate this package with:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0094 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement

Create `collaboration/work_packages/completions/WP-0094_codex_done.json` with at least:

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
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0094 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If readiness remains blocked by intentionally pending work, missing external dependencies, or a documented recipe exception, record that limitation in the completion receipt rather than claiming readiness.

## Demonstration Requirements

Document the exact commands run and observed status in the completion receipt. Include evidence for implementation-time checks, validation recipe behavior where applicable, and production-readiness compatibility.

## Merge Class
Class A.
