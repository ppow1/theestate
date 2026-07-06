# BATCH TASK WP-0203 — Office Controls Wave 1 Staged Foundation

## Codex Command
Read collaboration/work_packages/pending/WP-0203_BATCH_office_controls_wave_1_staged_foundation.md and do exactly what it says.

## Mode
SEQUENTIAL-BATCH over PARALLEL-STAGED work packages

## Mission
Execute the first Office of the Steward verb-surface implementation wave as one coordinated Codex run by completing the following related staged packages in order:

1. `collaboration/work_packages/pending/WP-0200_PARALLEL_STAGED_office_action_framework_command_dispatch_foundation.md`
2. `collaboration/work_packages/pending/WP-0201_PARALLEL_STAGED_settings_help_about_utility_controls.md`
3. `collaboration/work_packages/pending/WP-0202_PARALLEL_STAGED_work_packages_tab_controls.md`

These packages are intentionally related. WP-0200 stages the shared Office action framework foundation. WP-0201 and WP-0202 stage the first tab-control implementations that should align with that foundation. Treat them as one coordinated wave, but preserve each package's separate workstream directory, install manifest, completion receipt, and validation evidence.

## Critical Rule
Do not directly install these staged controls into active Office runtime files during this batch.

Each package must remain `PARALLEL-STAGED` and must place its implementation artifacts under its own workstream directory:

- `collaboration/workstreams/WP-0200/`
- `collaboration/workstreams/WP-0201/`
- `collaboration/workstreams/WP-0202/`

Staged work is not installed work. Active runtime integration will happen later through an explicit install-handoff package or reviewer-directed install.

## Why These Three Are Batched
These packages are safe to execute in one batch because they should not modify active shared Office runtime files directly.

They are related as follows:

- WP-0200 defines the shared action metadata, authority classes, confirmation behavior, command hook shape, and output-path reporting model.
- WP-0201 stages low-risk Settings, Help, and About controls using or aligning with that model.
- WP-0202 stages Work Packages tab controls using or aligning with that model while explicitly preventing silent work-package execution.

Do not let WP-0201 or WP-0202 invent incompatible action metadata if WP-0200 provides a usable staged pattern. If WP-0200 reveals that a different metadata shape is needed, document that once and keep WP-0201/WP-0202 aligned with the same vocabulary.

## Required Execution Order
Execute in this order:

### Step 1 — WP-0200
Read and complete:

`collaboration/work_packages/pending/WP-0200_PARALLEL_STAGED_office_action_framework_command_dispatch_foundation.md`

Expected outputs include:

- `collaboration/workstreams/WP-0200/install_manifest.json`
- staged action framework artifacts under `collaboration/workstreams/WP-0200/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0200_codex_done.json`

### Step 2 — WP-0201
Read and complete:

`collaboration/work_packages/pending/WP-0201_PARALLEL_STAGED_settings_help_about_utility_controls.md`

Expected outputs include:

- `collaboration/workstreams/WP-0201/install_manifest.json`
- staged Settings/Help/About utility control artifacts under `collaboration/workstreams/WP-0201/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0201_codex_done.json`

WP-0201 must align its action metadata and confirmation model with WP-0200 where practical.

### Step 3 — WP-0202
Read and complete:

`collaboration/work_packages/pending/WP-0202_PARALLEL_STAGED_work_packages_tab_controls.md`

Expected outputs include:

- `collaboration/workstreams/WP-0202/install_manifest.json`
- staged Work Packages tab control artifacts under `collaboration/workstreams/WP-0202/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0202_codex_done.json`

WP-0202 must align its action metadata and confirmation model with WP-0200 where practical.

## Batch-Level Output
In addition to the individual package outputs, create:

`collaboration/work_packages/completions/WP-0203_batch_done.json`

The batch completion artifact must include:

- `batch_work_package_id`: `WP-0203`
- `batch_title`: `Office Controls Wave 1 Staged Foundation`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- ordered package list
- per-package completion receipt paths
- per-package staged workstream paths
- per-package install manifest paths
- summary of cross-package alignment decisions
- any conflicts detected between WP-0200, WP-0201, and WP-0202
- validation commands run
- known limitations
- `staged_work_is_installed`: `false`
- `ready_for_ca_review`: `true`
- `merge_authority`: `ca_verified_auto_merge_allowed`

## Batch-Level Validation
Run or document these commands where available:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0200 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0201 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0202 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If individual validation recipes for WP-0200 through WP-0202 do not yet exist, document that limitation in each completion receipt and in `WP-0203_batch_done.json`.

## Conflict Surface Rules
Because these packages are staged, do not modify the shared active files unless absolutely necessary and explicitly justified:

- `src/estate/core/steward_command_center.py`
- `src/estate/cli/main.py`
- `src/estate/core/work_package_validation.py`
- `tests/test_steward_command_center.py`
- `tests/test_work_package_validation.py`

If active-file modification is necessary for validation of staged-work manifests only, keep it minimal, document it in the batch receipt, and preserve the fact that staged Office controls are not installed.

## Safety Rules
1. Do not execute pending work packages from the Office UI.
2. Do not add autonomous execution.
3. Do not make UI buttons equivalent to institutional permission.
4. Do not declare validation acceptance from UI state alone.
5. Do not mark Chief Architect review complete.
6. Do not install staged controls into active runtime files.
7. Do not add cloud calls, telemetry, or external service dependencies.
8. Keep all package outputs local-first, reviewable, and auditable.

## Acceptance Criteria
This batch is complete when:

1. WP-0200 is completed with staged artifacts, install manifest, and completion receipt.
2. WP-0201 is completed with staged artifacts, install manifest, and completion receipt.
3. WP-0202 is completed with staged artifacts, install manifest, and completion receipt.
4. WP-0201 and WP-0202 align with the WP-0200 staged action vocabulary where practical.
5. A batch-level completion artifact exists at `collaboration/work_packages/completions/WP-0203_batch_done.json`.
6. No staged control is installed into active Office runtime files by this batch.
7. The batch is ready for Chief Architect / Steward review and later install-handoff planning.

## Merge Class
Class A if this batch creates staged workstream artifacts, manifests, receipts, and validation notes only.

Escalate to Class B if active runtime files are modified beyond minimal validation support.
