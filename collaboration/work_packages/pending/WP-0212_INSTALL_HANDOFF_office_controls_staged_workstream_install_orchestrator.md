# INSTALL-HANDOFF TASK WP-0212 — Office Controls Staged Workstream Install Orchestrator

## Codex Command
Read collaboration/work_packages/pending/WP-0212_INSTALL_HANDOFF_office_controls_staged_workstream_install_orchestrator.md and do exactly what it says.

## Mode
INSTALL-HANDOFF

## Mission
Install the completed Office of the Steward staged control workstreams from Waves 1 through 3 into the active Office runtime when their staged artifacts are present, internally consistent, and conflict-reviewed.

This is not merely a planning package. This is the install handoff package.

Codex must inspect the staged workstreams, validate their manifests, detect conflicts, determine a safe install order, and then install the phases that are ready. If a phase is blocked by missing artifacts, incompatible staged designs, active-file conflicts, or failing validation, leave that phase staged and document the block. Do not use caution as a reason to avoid installation when the staged artifacts are valid and the risk is understood.

The goal is to move the Office verb-surface work from parallel staged artifacts into active runtime functionality while preserving reviewability, rollback, safety boundaries, and Chief Architect / Steward control.

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

All individual implementation packages were authored as `PARALLEL-STAGED` packages under the WP-0112 standard. Staged work is not installed work. WP-0212 exists to perform the controlled transition from staged work into installed Office functionality.

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

If some packages are not complete yet, do not fabricate their outputs. Install the ready phases that do not depend on missing work, and explicitly mark missing or dependent phases as blocked.

## Scope
Create and execute a controlled install handoff for the staged Office control workstreams.

In scope:

1. Inspect all available staged workstreams from WP-0200 through WP-0210.
2. Validate every available `install_manifest.json`.
3. Read each completion receipt where present.
4. Detect overlapping final install paths and expected active files.
5. Detect incompatible staged action metadata shapes.
6. Determine installation phases and order.
7. Install phases that are ready and conflict-reviewed.
8. Leave blocked phases staged with explicit reasons.
9. Create an install readiness and execution report.
10. Create a rollback plan.
11. Create or update active implementation files when a phase is ready.
12. Run validation after installed phases.
13. Create an install manifest for WP-0212 itself.
14. Create a completion receipt for WP-0212.

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
- `collaboration/workstreams/WP-0212/office_controls_install_execution_report.md`
- `collaboration/workstreams/WP-0212/office_controls_install_plan.json`
- `collaboration/workstreams/WP-0212/office_controls_conflict_matrix.json`
- `collaboration/workstreams/WP-0212/office_controls_rollback_plan.md`
- `collaboration/workstreams/WP-0212/post_install_validation.md`
- `collaboration/workstreams/WP-0212/validation_notes.md`

## Required Install Execution Report
Create:

`collaboration/workstreams/WP-0212/office_controls_install_execution_report.md`

The report must include:

1. Executive summary.
2. Which staged packages were found.
3. Which staged packages were missing.
4. Manifest validation results.
5. Completion receipt validation results.
6. Cross-package action vocabulary alignment status.
7. Conflict matrix summary.
8. Final install order.
9. Packages installed.
10. Packages left staged.
11. Blocking issues.
12. Non-blocking warnings.
13. Active files modified.
14. Rollback instructions.
15. Validation results after installation.
16. Required Chief Architect / Steward review decision.

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
- final action taken: `installed`, `left_staged`, `blocked`, or `skipped_not_present`

## Required Install Plan
Create:

`collaboration/workstreams/WP-0212/office_controls_install_plan.json`

The plan must define install phases.

Recommended phases:

### Phase 1 — Foundation
Install the Office action framework from WP-0200 when present and internally consistent.

### Phase 2 — Low-risk utilities
Install WP-0201 Settings/Help/About controls after the foundation.

### Phase 3 — Core operational controls
Install WP-0202 Work Packages and WP-0204 Validation controls if their staged metadata aligns.

### Phase 4 — Planning and communication controls
Install WP-0205 and WP-0206 if their staged metadata aligns and conflicts are manageable.

### Phase 5 — Board, resident, and AI service controls
Install WP-0208, WP-0209, and WP-0210 with extra authority review for resident and AI service surfaces. Do not start services or grant new resident authority.

The install plan must include:

- phase ID
- included work packages
- prerequisites
- active files to modify
- validation commands after phase
- rollback instructions
- approval requirement
- install status: `ready`, `blocked`, `installed`, `partial`, or `deferred`
- explanation for any phase not installed

## Installation Posture
Default posture is now active installation of ready phases, not planning-only.

Install a phase when all of these are true:

1. Required staged artifacts are present.
2. Required install manifest is present and valid.
3. Completion receipt is present or missing receipt is explicitly non-blocking with rationale.
4. Action metadata is compatible with the foundation vocabulary or can be normalized safely.
5. Active-file conflicts are understood and manageable.
6. The phase does not grant new authority or perform prohibited actions.
7. Rollback path is clear.
8. Validation can be run after installation.

Leave a phase staged when any of these are true:

1. Required artifacts are missing.
2. Metadata shapes are incompatible and cannot be normalized without guessing.
3. Active-file conflict cannot be resolved confidently.
4. The staged work attempts to grant authority outside WP-0118/WP-0200 boundaries.
5. Validation cannot be run or fails in a way that affects active functionality.

## Required Rollback Plan
Create:

`collaboration/workstreams/WP-0212/office_controls_rollback_plan.md`

The rollback plan must include:

- active files modified during installation
- staged artifact references used as install sources
- how to revert each installed phase
- validation commands to run after rollback
- generated/runtime artifacts to ignore or regenerate
- risks of partial install

## Required WP-0212 Install Manifest
Create:

`collaboration/workstreams/WP-0212/install_manifest.json`

It must include:

- `work_package_id`: `WP-0212`
- `workstream_mode`: `INSTALL-HANDOFF`
- staged artifact paths produced by WP-0212
- source staged workstreams inspected
- intended final install paths
- files modified during install
- manual install steps
- automated install steps, if any
- validation commands
- rollback notes
- dependency assumptions
- conflict risks
- generated artifacts to ignore or review
- authority and review requirements
- whether active installation was performed
- `staged_work_is_installed`: `true` if any staged controls are installed into active files, otherwise `false`

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

Also run appropriate tests for any active files modified. At minimum, if the Office command center is modified, run relevant command-center tests and a smoke command that renders or serves the Office payload.

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
- installed packages
- packages left staged
- install phases produced
- active files modified, if any
- staged artifact paths produced
- install manifest path
- conflict matrix path
- install plan path
- rollback plan path
- install execution report path
- validation commands run or skipped
- known limitations
- `staged_work_is_installed`: `true` if any staged controls are installed into active files, otherwise `false`
- `ready_for_ca_review`: `true`
- `merge_authority`: `ca_verified_auto_merge_allowed`

## Acceptance Criteria
WP-0212 is complete when:

1. Available staged Office control workstreams are inspected.
2. Missing workstreams are explicitly listed rather than invented.
3. Manifest validation is recorded.
4. A conflict matrix exists.
5. An install execution report exists.
6. An install plan exists with phases and final status.
7. Ready phases are installed unless a specific blocker is documented.
8. Blocked phases remain staged with reasons.
9. A rollback plan exists.
10. WP-0212 has its own install manifest.
11. WP-0212 has a completion receipt.
12. Active runtime installation, if performed, is explicitly documented, conflict-reviewed, validated, and treated as Class B.

## Merge Class
Class B if any active runtime files are modified or any staged controls are actually installed.

Class A only if no ready phases exist and the package creates install-handoff planning artifacts, conflict matrix, install plan, rollback plan, and completion receipt without modifying active runtime files.
