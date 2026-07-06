# BATCH TASK WP-0207 — Office Controls Wave 2 Operational Surfaces

## Codex Command
Read collaboration/work_packages/pending/WP-0207_BATCH_office_controls_wave_2_operational_surfaces.md and do exactly what it says.

## Mode
SEQUENTIAL-BATCH over PARALLEL-STAGED work packages

## Mission
Execute the second Office of the Steward verb-surface implementation wave as one coordinated Codex run by completing the following related staged packages in order:

1. `collaboration/work_packages/pending/WP-0204_PARALLEL_STAGED_validation_tab_controls.md`
2. `collaboration/work_packages/pending/WP-0205_PARALLEL_STAGED_mission_control_projects_roadmap_controls.md`
3. `collaboration/work_packages/pending/WP-0206_PARALLEL_STAGED_mailboxes_recalls_notifications_controls.md`

These packages are intentionally related. They convert the Office's core operational surfaces into staged, safe action/control designs while preserving the WP-0112 staged-work model and avoiding active runtime installation.

## Critical Rule
Do not directly install these staged controls into active Office runtime files during this batch.

Each package must remain `PARALLEL-STAGED` and must place its implementation artifacts under its own workstream directory:

- `collaboration/workstreams/WP-0204/`
- `collaboration/workstreams/WP-0205/`
- `collaboration/workstreams/WP-0206/`

Staged work is not installed work. Active runtime integration will happen later through an explicit install-handoff package or reviewer-directed install.

## Why These Three Are Batched
These packages are safe to execute in one batch because they should stage their work under isolated workstream directories rather than modifying shared Office files directly.

They are related as follows:

- WP-0204 stages Validation controls for evidence inspection, command copying, validation execution design, production-readiness refresh design, and validation observation drafting.
- WP-0205 stages Mission Control, Projects, and Roadmap controls for source inspection, refresh, warning-to-draft, prioritization/review requests, and planning-surface exports.
- WP-0206 stages Mailboxes, Recalls, and Notifications controls for inspection, local acknowledgement, reply/request drafting, routing, and export.

If WP-0200's staged action vocabulary is available, align all three packages with it. If WP-0200 is not yet completed or not visible in the working branch, use the WP-0118 action vocabulary directly and document the temporary alignment assumption in the batch receipt.

## Required Execution Order
Execute in this order:

### Step 1 — WP-0204
Read and complete:

`collaboration/work_packages/pending/WP-0204_PARALLEL_STAGED_validation_tab_controls.md`

Expected outputs include:

- `collaboration/workstreams/WP-0204/install_manifest.json`
- staged Validation tab control artifacts under `collaboration/workstreams/WP-0204/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0204_codex_done.json`

### Step 2 — WP-0205
Read and complete:

`collaboration/work_packages/pending/WP-0205_PARALLEL_STAGED_mission_control_projects_roadmap_controls.md`

Expected outputs include:

- `collaboration/workstreams/WP-0205/install_manifest.json`
- staged Mission Control, Projects, and Roadmap control artifacts under `collaboration/workstreams/WP-0205/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0205_codex_done.json`

### Step 3 — WP-0206
Read and complete:

`collaboration/work_packages/pending/WP-0206_PARALLEL_STAGED_mailboxes_recalls_notifications_controls.md`

Expected outputs include:

- `collaboration/workstreams/WP-0206/install_manifest.json`
- staged Mailboxes, Recalls, and Notifications control artifacts under `collaboration/workstreams/WP-0206/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0206_codex_done.json`

## Batch-Level Output
In addition to the individual package outputs, create:

`collaboration/work_packages/completions/WP-0207_batch_done.json`

The batch completion artifact must include:

- `batch_work_package_id`: `WP-0207`
- `batch_title`: `Office Controls Wave 2 Operational Surfaces`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- ordered package list
- per-package completion receipt paths
- per-package staged workstream paths
- per-package install manifest paths
- summary of cross-package alignment decisions
- whether WP-0200 staged vocabulary was available and used
- any conflicts detected between WP-0204, WP-0205, and WP-0206
- validation commands run
- known limitations
- `staged_work_is_installed`: `false`
- `ready_for_ca_review`: `true`
- `merge_authority`: `ca_verified_auto_merge_allowed`

## Batch-Level Validation
Run or document these commands where available:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0204 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0205 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0206 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If individual validation recipes for WP-0204 through WP-0206 do not yet exist, document that limitation in each completion receipt and in `WP-0207_batch_done.json`.

## Conflict Surface Rules
Because these packages are staged, do not modify the shared active files unless absolutely necessary and explicitly justified:

- `src/estate/core/steward_command_center.py`
- `src/estate/cli/main.py`
- `src/estate/core/work_package_validation.py`
- `src/estate/core/production_readiness_validation.py`
- `src/estate/core/validation_observations.py`
- `src/estate/core/steward_dashboard.py`
- `src/estate/core/operations_board.py`
- `src/estate/core/dependency_graph.py`
- `src/estate/core/mailbox_index.py`
- `src/estate/core/collaboration_messages.py`
- `src/estate/core/notification_router.py`
- `src/estate/core/operations_notification_center.py`
- `src/estate/core/decision_queue.py`
- `tests/test_steward_command_center.py`
- `tests/test_work_package_validation.py`

If active-file modification is necessary for validation of staged-work manifests only, keep it minimal, document it in the batch receipt, and preserve the fact that staged Office controls are not installed.

## Safety Rules
1. Do not install staged controls into active runtime files.
2. Do not make UI buttons equivalent to institutional permission.
3. Do not declare validation acceptance from UI state alone.
4. Do not make Mission Control, Projects, or Roadmap summaries authoritative.
5. Do not treat local acknowledgement as source closure.
6. Do not send replies, approve reviews, close recalls, or route decisions without authority.
7. Do not add autonomous execution.
8. Do not add cloud calls, telemetry, or external service dependencies.
9. Keep all package outputs local-first, reviewable, and auditable.

## Acceptance Criteria
This batch is complete when:

1. WP-0204 is completed with staged artifacts, install manifest, and completion receipt.
2. WP-0205 is completed with staged artifacts, install manifest, and completion receipt.
3. WP-0206 is completed with staged artifacts, install manifest, and completion receipt.
4. The three packages use a consistent action/authority vocabulary, preferably aligned with WP-0200 if available.
5. A batch-level completion artifact exists at `collaboration/work_packages/completions/WP-0207_batch_done.json`.
6. No staged control is installed into active Office runtime files by this batch.
7. The batch is ready for Chief Architect / Steward review and later install-handoff planning.

## Merge Class
Class A if this batch creates staged workstream artifacts, manifests, receipts, and validation notes only.

Escalate to Class B if active runtime files are modified beyond minimal validation support.
