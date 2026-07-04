# SERIES TASK WP-0098 — Operations Center Launch Script

## Codex Command
Read `collaboration/work_packages/pending/WP-0098_SERIES_operations_center_launch_script.md` and do exactly what it says.

## Mode

SERIES

## Mission
Create the Steward-facing local launch script for the Estate Operations Center so the control-room interface can be started from the Estate workspace with one clear operator action.

## Background

This work package remains a pending backlog item. WP-0102 added this background section to align the file with the Codex Task Template Standard while preserving the original mission and scope.

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


## WP-0102 Template Retrofit Notice

This section was added by WP-0102 as a mechanical template retrofit. It preserves the original mission and scope above. This pending package remains authored and queued; it is not implemented, validated, operationally validated, approved, or institutionalized by this retrofit.

## Out of Scope

- Do not change the original mission or core scope of WP-0098.
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
- Create `collaboration/work_packages/completions/WP-0098_codex_done.json`.
- Add or update the registered validation recipe for `WP-0098` unless this file explicitly states that the recipe is not applicable.

## Validation Recipe Requirement

Add or update the validation recipe for WP-0098. The recipe must be registered in the existing validation framework and must not return `no_recipe`. Classify checks as required or observational, use local-first non-destructive commands, and ensure future validation can evaluate this package with:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0098 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Codex Completion Receipt Requirement

Create `collaboration/work_packages/completions/WP-0098_codex_done.json` with at least:

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
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0098 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If readiness remains blocked by intentionally pending work, missing external dependencies, or a documented recipe exception, record that limitation in the completion receipt rather than claiming readiness.

## Demonstration Requirements

Document the exact commands run and observed status in the completion receipt. Include evidence for implementation-time checks, validation recipe behavior where applicable, and production-readiness compatibility.

## Merge Class
Class A unless command authority, runtime execution, or governance semantics are changed; escalate to Class B if those boundaries are altered.
