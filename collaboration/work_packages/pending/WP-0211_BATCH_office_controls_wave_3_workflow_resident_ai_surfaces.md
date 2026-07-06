# BATCH TASK WP-0211 — Office Controls Wave 3 Workflow, Resident, and AI Surfaces

## Codex Command
Read collaboration/work_packages/pending/WP-0211_BATCH_office_controls_wave_3_workflow_resident_ai_surfaces.md and do exactly what it says.

## Mode
SEQUENTIAL-BATCH over PARALLEL-STAGED work packages

## Mission
Execute the third Office of the Steward verb-surface implementation wave as one coordinated Codex run by completing the following related staged packages in order:

1. `collaboration/work_packages/pending/WP-0208_PARALLEL_STAGED_daily_board_parking_lot_controls.md`
2. `collaboration/work_packages/pending/WP-0209_PARALLEL_STAGED_resident_conversation_controls.md`
3. `collaboration/work_packages/pending/WP-0210_PARALLEL_STAGED_ai_services_model_controls.md`

These packages complete the staged Office verb-surface backlog from WP-0118 by covering the remaining board/workflow, resident interaction, and AI services/model control surfaces. Treat them as one coordinated wave while preserving each package's separate workstream directory, install manifest, completion receipt, and validation evidence.

## Critical Rule
Do not directly install these staged controls into active Office runtime files during this batch.

Each package must remain `PARALLEL-STAGED` and must place its implementation artifacts under its own workstream directory:

- `collaboration/workstreams/WP-0208/`
- `collaboration/workstreams/WP-0209/`
- `collaboration/workstreams/WP-0210/`

Staged work is not installed work. Active runtime integration will happen later through an explicit install-handoff package or reviewer-directed install.

## Why These Three Are Batched
These packages are safe to execute in one batch because they stage their work under isolated workstream directories rather than modifying shared Office files directly.

They are related as follows:

- WP-0208 stages Daily Board and Parking Lot controls for refresh, source inspection, local review markers, note drafting, proposal drafting, review requests, and local exports.
- WP-0209 stages Alfred, Helen, and Resident Conversations controls for session start/open/export, resident surface inspection, command copying, resident request drafting, authority inspection, and audited redaction/forget design.
- WP-0210 stages AI Services / Model controls for local manifest inspection, rediscovery/provider-sync design, copy-only service/model commands, approval request drafting, audit inspection, read-only resident/model assignment inspection, and local exports.

If WP-0200's staged action vocabulary is available, align all three packages with it. If WP-0200 is not yet completed or not visible in the working branch, use the WP-0118 action vocabulary directly and document the temporary alignment assumption in the batch receipt.

## Required Execution Order
Execute in this order:

### Step 1 — WP-0208
Read and complete:

`collaboration/work_packages/pending/WP-0208_PARALLEL_STAGED_daily_board_parking_lot_controls.md`

Expected outputs include:

- `collaboration/workstreams/WP-0208/install_manifest.json`
- staged Daily Board and Parking Lot control artifacts under `collaboration/workstreams/WP-0208/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0208_codex_done.json`

### Step 2 — WP-0209
Read and complete:

`collaboration/work_packages/pending/WP-0209_PARALLEL_STAGED_resident_conversation_controls.md`

Expected outputs include:

- `collaboration/workstreams/WP-0209/install_manifest.json`
- staged Resident Conversation control artifacts under `collaboration/workstreams/WP-0209/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0209_codex_done.json`

### Step 3 — WP-0210
Read and complete:

`collaboration/work_packages/pending/WP-0210_PARALLEL_STAGED_ai_services_model_controls.md`

Expected outputs include:

- `collaboration/workstreams/WP-0210/install_manifest.json`
- staged AI Services / Model control artifacts under `collaboration/workstreams/WP-0210/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0210_codex_done.json`

## Batch-Level Output
In addition to the individual package outputs, create:

`collaboration/work_packages/completions/WP-0211_batch_done.json`

The batch completion artifact must include:

- `batch_work_package_id`: `WP-0211`
- `batch_title`: `Office Controls Wave 3 Workflow, Resident, and AI Surfaces`
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
- any conflicts detected between WP-0208, WP-0209, and WP-0210
- validation commands run
- known limitations
- `staged_work_is_installed`: `false`
- `ready_for_ca_review`: `true`
- `merge_authority`: `ca_verified_auto_merge_allowed`

## Batch-Level Validation
Run or document these commands where available:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0208 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0209 --json
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0210 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If individual validation recipes for WP-0208 through WP-0210 do not yet exist, document that limitation in each completion receipt and in `WP-0211_batch_done.json`.

## Conflict Surface Rules
Because these packages are staged, do not modify the shared active files unless absolutely necessary and explicitly justified:

- `src/estate/core/steward_command_center.py`
- `src/estate/cli/main.py`
- `src/estate/core/daily_board_integration.py`
- `src/estate/core/morning_briefing.py`
- `src/estate/core/operations_board.py`
- `operations/boards/daily_board.md`
- `operations/boards/active_work.md`
- `operations/boards/parking_lot.md`
- `src/estate/core/resident_interaction.py`
- `src/estate/core/resident_conversation_sessions.py`
- `src/estate/core/resident_authority.py`
- `src/estate/core/resident_presence.py`
- `src/estate/core/alfred.py`
- `src/estate/core/alfred_duty.py`
- `src/estate/core/helen_duty.py`
- `src/estate/core/discovery.py`
- `src/estate/core/discovery_catalog.py`
- `src/estate/core/discovery_cycle.py`
- `src/estate/core/provider_sync.py`
- `src/estate/core/services.py`
- `src/estate/core/service_layer.py`
- `runtime/ai_services/registry.json`
- `runtime/ai_services/audit_log.jsonl`
- `tests/test_steward_command_center.py`
- `tests/test_resident_interaction.py`

If active-file modification is necessary for validation of staged-work manifests only, keep it minimal, document it in the batch receipt, and preserve the fact that staged Office controls are not installed.

## Safety Rules
1. Do not install staged controls into active runtime files.
2. Do not make UI buttons equivalent to institutional permission.
3. Do not convert Parking Lot items into executable work packages without authority.
4. Do not treat local review markers as authoritative closure.
5. Do not let residents silently execute work packages, mutate governance, mutate personnel records, validate institutionally, or merge.
6. Do not start/stop/load AI services or models from this batch.
7. Do not treat approval requests as approvals.
8. Do not delete board entries, Parking Lot entries, conversation history, messages, models, services, or runtime artifacts.
9. Do not add cloud calls, telemetry, or external service dependencies.
10. Keep all package outputs local-first, reviewable, and auditable.

## Acceptance Criteria
This batch is complete when:

1. WP-0208 is completed with staged artifacts, install manifest, and completion receipt.
2. WP-0209 is completed with staged artifacts, install manifest, and completion receipt.
3. WP-0210 is completed with staged artifacts, install manifest, and completion receipt.
4. The three packages use a consistent action/authority vocabulary, preferably aligned with WP-0200 if available.
5. A batch-level completion artifact exists at `collaboration/work_packages/completions/WP-0211_batch_done.json`.
6. No staged control is installed into active Office runtime files by this batch.
7. The batch is ready for Chief Architect / Steward review and later install-handoff planning.

## Merge Class
Class A if this batch creates staged workstream artifacts, manifests, receipts, and validation notes only.

Escalate to Class B if active runtime files are modified beyond minimal validation support.
