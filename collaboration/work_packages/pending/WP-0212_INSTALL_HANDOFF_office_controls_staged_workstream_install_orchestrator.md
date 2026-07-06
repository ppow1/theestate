# INSTALL-HANDOFF TASK WP-0212 — Office Controls Staged Workstream Install Orchestrator

## Codex Command
Read collaboration/work_packages/pending/WP-0212_INSTALL_HANDOFF_office_controls_staged_workstream_install_orchestrator.md and do exactly what it says.

## Mode
INSTALL-HANDOFF

## Mission
Create a controlled installation handoff for the Office of the Steward staged control workstreams created by Waves 1 through 3.

This package must not blindly install everything. It must inspect the staged workstreams, validate their manifests, detect conflicts, determine a safe install order, identify what can be installed now, identify what must remain staged, and produce an explicit installation plan and optional install artifacts.

The goal is to move from parallel staged Office control work toward active runtime integration without losing reviewability, rollback, safety boundaries, or Chief Architect / Steward control.

## Background
The Office verb-surface implementation was intentionally split into staged waves to avoid conflicts while multiple architects and workers operate in parallel.

Wave 1:

- WP-0200 — Office Action Framework / Command Dispatch Foundation
- WP-0201 — Settings, Help, About Utility Controls
- WP-0202 — Work Packages Tab Controls
- WP-0203 — Batch wrapper for Wave 1

Wave 2:

- WP-0204 — Validation Tab Controls
- WP-0205 — Mission Control, Projects, and Roadmap Controls
- WP-0206 — Mailboxes, Recalls, and Notifications Controls
- WP-0207 — Batch wrapper for Wave 2

Wave 3:

- WP-0208 — Daily Board and Parking Lot Controls
- WP-0209 — Resident Conversation Controls
- WP-0210 — AI Services / Model Controls
- WP-0211 — Batch wrapper for Wave 3

All individual implementation packages were authored as `PARALLEL-STAGED` packages under the WP-0112 standard. That means their staged artifacts are not installed work. This WP-0212 package creates the install handoff mechanism and installation plan.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3:

- WP-0200 through WP-0250

Do not renumber this package based on GitHub search results.

## Preconditions
Before executing this package, inspect whether the batch packages have completed and produced their staged outputs.

Expected completion artifacts:

- `collaboration/work_packages/completions/WP-0200_codex_done.json`
- `collaboration/work_packages/completions/WP-0201_codex_done.json`
- `collaboration/work_packages/completions/WP-0202_codex_done.json`
- `collaboration/work_packages/completions/WP-0203_batch_done.json`
- `collaboration/work_packages/completions/WP-0204_codex_done.json`
- `collaboration/work_packages/completions/WP-0205_codex_done.json`
- `collaboration/work_packages/completions/WP-0206_codex_done.json`
- `collaboration/work_packages/completions/WP-0207_batch_done.json`
- `collaboration/work_packages/completions/WP-0208_codex_done.json`
- `collaboration/work_packages/completions/WP-0209_codex_done.json`
- `collaboration/work_packages/completions/WP-0210_codex_done.json`
- `collaboration/work_packages/completions/WP-0211_batch_done.json`

Expected staged manifests:

- `collaboration/workstreams/WP-0200/install_manifest.json`
- `collaboration/workstreams/WP-0201/install_manifest.json`
- `collaboration/workstreams/WP-0202/install_manifest.json`
- `collaboration/workstreams/WP-0204/install_manifest.json`
- `collaboration/workstreams/WP-0205/install_manifest.json`
- `collaboration/workstreams/WP-0206/install_manifest.json`
- `collaboration/workstreams/WP-0208/install_manifest.json`
- `collaboration/workstreams/WP-0209/install_manifest.json`
- `collaboration/workstreams/WP-0210/install_manifest.json`

If some packages are not complete yet, do not fabricate their outputs. Record missing prerequisites and produce a partial install readiness report rather than forcing installation.

## Scope
Create an install handoff mechanism and integration plan for the staged Office control workstreams.

In scope:

1. Inspect all available staged workstreams from WP-0200 through WP-0210.
2. Validate every available `install_manifest.json`.
3. Read each completion receipt where present.
4. Detect overlapping final install paths and expected active files.
5. Detect incompatible staged action metadata shapes.
6. Determine installation phases and order.
7. Create an install readiness report.
8. Create a rollback plan.
9. Create optional proposed install artifacts or patch bundle under `collaboration/workstreams/WP-0212/`.
10. Create an install manifest for WP-0212 itself.
11. Create a completion receipt for WP-0212.

## Out of Scope
Do not blindly overwrite `src/estate/core/steward_command_center.py` or any active runtime file.

Do not install staged work unless all source staged artifacts required for that specific install phase are present, internally consistent, and conflict-reviewed.

Do not merge incompatible staged artifacts by guessing.

Do not delete staged workstream artifacts.

Do not execute pending work packages from the Office UI.

Do not grant resident, validation, service, governance, Chief Architect, merge, or Steward authority.

Do not start or stop AI services.

Do not add cloud calls, telemetry, or external service dependencies.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Workstream Directory
Create:

`collaboration/workstreams/WP-0212/`

Expected artifacts may include:

- `collaboration/workstreams/WP-0212/install_manifest.json`
- `collaboration/workstreams/WP-0212/office_controls_install_readiness_report.md`
- `collaboration/workstreams/WP-0212/office_controls_install_plan.json`
- `collaboration/workstreams/WP-0212/office_controls_conflict_matrix.json`
- `collaboration/workstreams/WP-0212/office_controls_rollback_plan.md`
- `collaboration/workstreams/WP-0212/proposed_install/README.md`
- `collaboration/workstreams/WP-0212/proposed_install/patch_notes.md`
- `collaboration/workstreams/WP-0212/validation_notes.md`

Use the structure that best fits the repository, but keep the handoff artifacts isolated and reviewable.

## Required Install Readiness Report
Create:

`collaboration/workstreams/WP-0212/office_controls_install_readiness_report.md`

The report must include:

1. Executive summary.
2. Which staged packages were found.
3. Which staged packages were missing.
4. Manifest validation results.
5. Completion receipt validation results.
6. Cross-package action vocabulary alignment status.
7. Conflict matrix summary.
8. Recommended install order.
9. Packages safe to install now.
10. Packages that must remain staged.
11. Blocking issues.
12. Non-blocking warnings.
13. Rollback considerations.
14. Required Chief Architect / Steward review decision.

## Required Conflict Matrix
Create:

`collaboration/workstreams/WP-0212/office_controls_conflict_matrix.json`

The conflict matrix must summarize, for each staged package:

- work package ID
- manifest path
- staged artifact paths
- intended final install paths
- files expected to be modified during install
- dependency assumptions
- conflict risks
- whether it overlaps with another staged package
- whether it overlaps with known active CA4 work if discoverable from available repository artifacts
- recommended action: `install_now`, `install_later`, `requires_review`, `blocked_missing_artifact`, or `blocked_conflict`

## Required Install Plan
Create:

`collaboration/workstreams/WP-0212/office_controls_install_plan.json`

The plan must define install phases. Recommended phases:

### Phase 1 — Foundation
Install or propose installation of the Office action framework from WP-0200.

### Phase 2 — Low-risk utilities
Install or propose installation of WP-0201 Settings/Help/About controls after the foundation.

### Phase 3 — Core operational controls
Install or propose installation of WP-0202 Work Packages and WP-0204 Validation controls, if their staged metadata aligns.

### Phase 4 — Planning and communication controls
Install or propose installation of WP-0205 and WP-0206.

### Phase 5 — Board, resident, and AI service controls
Install or propose installation of WP-0208, WP-0209, and WP-0210, with extra authority review for resident and AI service surfaces.

The install plan must include:

- phase ID
- included work packages
- prerequisites
- active files to modify
- validation commands after phase
- rollback instructions
- approval requirement
- install status: `proposed`, `ready`, `blocked`, `installed`, or `deferred`

Unless the repository state clearly supports safe active installation, leave phases as `proposed` or `ready` rather than `installed`.

## Required Rollback Plan
Create:

`collaboration/workstreams/WP-0212/office_controls_rollback_plan.md`

The rollback plan must include:

- active files that would be modified during installation
- staged artifact references used as install sources
- how to revert each phase
- validation commands to run after rollback
- generated/runtime artifacts to ignore or regenerate
- risks of partial install

## Optional Proposed Install Artifacts
If the staged artifacts are complete enough to build an actual install patch, place proposed install artifacts under:

`collaboration/workstreams/WP-0212/proposed_install/`

Do not apply the proposed install directly unless all safety conditions are met and the package explicitly records why installation is safe.

If active installation is performed, this package must escalate to Class B, document exact active files modified, run full validation, and produce post-install evidence.

Default posture: create the install plan and proposed install artifacts; do not install active runtime changes yet.

## Required WP-0212 Install Manifest
Create:

`collaboration/workstreams/WP-0212/install_manifest.json`

It must include:

- `work_package_id`: `WP-0212`
- `workstream_mode`: `INSTALL-HANDOFF`
- staged artifact paths produced by WP-0212
- source staged workstreams inspected
- intended final install paths
- files expected to be modified during eventual install
- manual install steps
- automated install steps, if any
- validation commands
- rollback notes
- dependency assumptions
- conflict risks
- generated artifacts to ignore or review
- authority and review requirements
- whether active installation was performed
- `staged_work_is_installed`: `false` unless active files are actually updated

## Required Validation Commands
Run or document equivalent validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0200 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0201 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0202 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0204 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0205 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0206 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0208 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0209 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0210 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If some workstreams are missing, record the command as skipped with reason.

If WP-0212 adds a validation recipe, also run:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0212 --json
```

## Required Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0212_codex_done.json`

It must include:

- `work_package_id`: `WP-0212`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `workstream_mode`: `INSTALL-HANDOFF`
- source staged packages inspected
- missing staged packages
- install readiness status
- install phases produced
- active files modified, if any
- staged artifact paths produced
- install manifest path
- conflict matrix path
- install plan path
- rollback plan path
- validation commands run or skipped
- known limitations
- `staged_work_is_installed`: `false` unless active files are actually updated
- `ready_for_ca_review`: `true`
- `merge_authority`: `ca_verified_auto_merge_allowed`

## Acceptance Criteria
WP-0212 is complete when:

1. Available staged Office control workstreams are inspected.
2. Missing workstreams are explicitly listed rather than invented.
3. Manifest validation is recorded.
4. A conflict matrix exists.
5. An install readiness report exists.
6. An install plan exists with phases and status.
7. A rollback plan exists.
8. WP-0212 has its own install manifest.
9. WP-0212 has a completion receipt.
10. Active runtime installation is either not performed, or if performed, is explicitly justified, conflict-reviewed, validated, and documented as Class B.

## Merge Class
Class A if this package creates install-handoff planning artifacts, conflict matrix, install plan, rollback plan, and completion receipt only.

Escalate to Class B if any active runtime files are modified or any staged controls are actually installed.
