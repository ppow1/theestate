# PARALLEL-STAGED TASK WP-0210 — AI Services / Model Controls

## Codex Command
Read collaboration/work_packages/pending/WP-0210_PARALLEL_STAGED_ai_services_model_controls.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Design and stage safe AI Services / Model controls for the Office of the Steward without directly installing changes into active Office runtime files.

This package implements the WP-0118-F7 follow-up slice: AI Services / Model Controls. It must produce staged, reviewable artifacts under `collaboration/workstreams/WP-0210/`, including proposed UI/control metadata, proposed code or patch structure, tests or staged test plan, validation notes, and an install manifest.

The AI Services / Models surface should become a safe local control surface for manifest inspection, rediscovery refresh, command copying, approval-request drafting, and model/service status inspection before any future direct process-control adapters are introduced.

## Background
WP-0118 identified AI Services / Models as a high-risk Office verb surface. Proposed verbs include rediscover, inspect manifest, copy start/stop/load commands, request approval, and later gated process-control adapters. This package must stage the inspection and request surfaces first, not service process control.

WP-0200 stages the shared Office action framework foundation. WP-0210 should align with the WP-0200 staged vocabulary where practical, but must not assume WP-0200 is already installed.

Because Chief Architect #4 and other workers may be touching Office UI, discovery, model registry, or service files concurrently, WP-0210 follows the WP-0112 parallel workstream standard. This package stages proposed implementation rather than modifying active Office runtime files directly.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3: WP-0200 through WP-0250.

Do not renumber this package based on GitHub search results.

## Scope
Create staged implementation artifacts for AI Services / Model controls.

In scope:

1. Inspect current AI Services / Models surfaces in the Office implementation.
2. Inspect existing AI service registry, discovery, provider sync, Ollama sync, model inventory, approval, and audit artifacts/modules.
3. Stage proposed controls for AI Services / Models only.
4. Align action metadata with WP-0200 staged action vocabulary where practical.
5. Create staged tests or a test plan.
6. Create `collaboration/workstreams/WP-0210/install_manifest.json`.
7. Create `collaboration/work_packages/completions/WP-0210_codex_done.json`.

## Out of Scope
Do not directly modify active Office runtime files in this package.

Do not start, stop, load, unload, install, delete, or download models/services from the Office in this package.

Do not add direct process control adapters.

Do not add cloud calls, external API calls, telemetry, or remote model/service dependencies.

Do not mutate service approval state except as a staged draft/request design.

Do not assign a model backend to Alfred, Helen, or any resident unless existing source state already supports read-only inspection.

Do not bypass Steward authority, approval workflow, resident action authority, validation, governance, or merge authority.

Do not implement controls for Work Packages, Validation, Mission Control, Parking Lot, Residents, Mailboxes, Settings, Help, or About except where needed as read-only references.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Staging Location
All staged artifacts must live under:

`collaboration/workstreams/WP-0210/`

Expected staged paths may include:

- `collaboration/workstreams/WP-0210/proposed/ai_services_model_controls.md`
- `collaboration/workstreams/WP-0210/proposed/action_metadata.json`
- `collaboration/workstreams/WP-0210/proposed/src/estate/core/office_ai_service_actions.py`
- `collaboration/workstreams/WP-0210/proposed/tests/test_office_ai_service_actions.py`
- `collaboration/workstreams/WP-0210/install_manifest.json`
- `collaboration/workstreams/WP-0210/validation_notes.md`

## Required Controls to Stage
Stage controls for AI Services / Models only.

### AI Services / Models
Proposed controls should include:

1. Inspect service/model manifest
   - Open/read local service registry, discovery catalog, provider/model inventory, approvals, audit references, and related source artifacts where available.
   - Safe read-only.

2. Refresh rediscovery, staged design only
   - Design how the UI would run existing local discovery/refresh commands and report generated output paths.
   - Safe local generated-artifact update after explicit confirmation.
   - Must not download/install external services.

3. Sync local model provider inventory, staged design only
   - Design how the UI would invoke existing local provider-sync commands where supported.
   - Safe local generated-artifact update after confirmation.
   - Must clearly show working directory, command, expected output paths, and failure behavior.

4. Copy start/stop/load commands
   - Copy-only command affordances for approved local service/model commands where known.
   - Safe read-only by default.
   - Must be visually distinct from execution.

5. Request service/model approval
   - Draft/queue approval request through existing authority path.
   - Authority-gated.
   - Does not approve or start service.

6. Inspect approval/audit history
   - Safe read-only inspection of existing approval and audit artifacts.

7. Inspect resident/model assignment state, if present
   - Safe read-only.
   - Must not assign or change model backend.

8. Export AI services snapshot
   - Local-only snapshot with source references and sensitivity warning.
   - Safe read-only or generated-artifact update after confirmation.

## Required Action Metadata
For each proposed control, include action metadata with:

- action ID
- label
- target tab/service/model/provider when applicable
- description
- action class
- authority/safety class
- confirmation requirement
- reads artifacts
- writes artifacts
- command hook or handler reference
- expected output paths
- failure behavior
- local-only/no-upload guarantee
- explicit statement whether the action is copy-only, generated-artifact update, approval request, or future-gated process control

Use WP-0118 and WP-0200 vocabulary.

## Required Safety Rules
The staged design must enforce or describe:

1. Copying a command is not executing a command.
2. Approval request is not approval.
3. Rediscovery refresh is not model installation or service startup.
4. Provider sync must be local-only and must report generated artifact paths.
5. Future start/stop/load actions must remain authority-gated and absent or explicitly unavailable until a process adapter and approval route exist.
6. Model/backend assignment state is read-only unless a later approved package designs mutation authority.
7. Export bundles include sensitivity warnings and remain local-only.

## Required Install Manifest
Create:

`collaboration/workstreams/WP-0210/install_manifest.json`

The manifest must follow the WP-0112 standard and include staged artifact paths, intended final install paths, expected modified files, manual/automated install steps, validation commands, rollback notes, dependency assumptions, conflict risks, generated artifacts to ignore/review, authority/review requirements, and `staged_work_is_installed: false`.

## Conflict Surface Declaration
Expected conflict surface:

- `src/estate/core/steward_command_center.py` — likely future UI integration target
- `src/estate/core/discovery.py` — possible read-only/helper reference
- `src/estate/core/discovery_catalog.py` — possible read-only/helper reference
- `src/estate/core/discovery_cycle.py` — possible rediscovery helper reference
- `src/estate/core/provider_sync.py` — possible provider-sync helper reference
- `src/estate/core/services.py` — possible registry/helper reference
- `src/estate/core/service_layer.py` — possible status/capability helper reference
- `src/estate/cli/main.py` — possible command registry reference
- `runtime/ai_services/registry.json` — generated/runtime reference; do not mutate directly except through existing generator design
- `runtime/ai_services/audit_log.jsonl` — audit reference; do not mutate directly in this package
- `tests/test_steward_command_center.py` — likely future integration tests

Risk class: high, because future install may touch shared Office UI and AI service/discovery surfaces, and service controls can affect host resources if mishandled.

Packages that can run in parallel:

- Other `PARALLEL-STAGED` tab-control packages that stage under their own workstream directories.

Packages that should complete before install:

- WP-0118 complete and merged.
- WP-0200 reviewed or installed as action framework foundation.
- Any active CA4 repair touching Office UI, discovery, AI services, or model registry reviewed for conflicts.

## Required Tests / Staged Tests
Provide staged tests or a test plan proving:

- Manifest inspection and approval/audit inspection are safe read-only.
- Rediscovery/provider sync designs require confirmation and report output paths.
- Start/stop/load command controls are copy-only by default and not executable.
- Approval request does not approve or start a service.
- Resident/model assignment inspection is read-only.
- Export snapshot includes sensitivity warning and local-only/no-upload posture.
- Future direct process controls remain authority-gated/unavailable.

## Required Validation Commands
Run or document equivalent staged validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0210 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0210 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If WP-0210 has no validation recipe yet because staged packages are not fully integrated into validation, document that limitation in the completion receipt.

## Required Outputs
Create or update:

- `collaboration/workstreams/WP-0210/install_manifest.json`
- staged proposed AI Services / Model control artifacts under `collaboration/workstreams/WP-0210/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0210_codex_done.json`

Do not install staged files into active runtime paths in this package.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0210_codex_done.json`

It must include work_package_id, codex_status, completed_at, branch, pull_request_url or reason, summary, workstream mode, staged artifact paths, install manifest path, intended install paths, conflict risks, controls staged, files changed, tests/validation run, known limitations, `staged_work_is_installed: false`, `ready_for_ca_review: true`, and `merge_authority: ca_verified_auto_merge_allowed`.

## Acceptance Criteria
WP-0210 is complete when staged AI Services / Model control artifacts exist, every staged control has action metadata/authority classification/confirmation behavior/local-only posture, direct service process controls remain absent/future-gated, an install manifest exists, risks are explicit, tests or staged test plan exist, completion receipt exists, and active Office runtime files are not directly installed.

## Merge Class
Class A if this package only creates staged workstream artifacts, install manifest, tests/test plan, and completion receipt.

Escalate to Class B if active runtime files are modified or the package attempts to install controls directly.
