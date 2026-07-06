# PARALLEL-STAGED TASK WP-0204 — Validation Tab Controls

## Codex Command
Read collaboration/work_packages/pending/WP-0204_PARALLEL_STAGED_validation_tab_controls.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Design and stage safe Validation tab controls for the Office of the Steward without directly installing changes into active Office runtime files.

This package implements the WP-0118-F3 follow-up slice: Validation Tab Controls. It must produce staged, reviewable artifacts under `collaboration/workstreams/WP-0204/`, including proposed UI/control metadata, proposed code or patch structure, tests or staged test plan, validation notes, and an install manifest.

The Validation tab should become a safe operational evidence surface: run or copy validation commands, open reports, inspect failure evidence, create validation observations, and refresh production-readiness artifacts while explicitly distinguishing validation evidence from institutional acceptance.

## Background
WP-0118 identified Validation as a key Office verb surface. Proposed verbs include running recipes, running production readiness, opening reports, copying failing commands, and creating validation observations. WP-0200 stages the shared Office action framework foundation. WP-0204 should align with the WP-0200 staged vocabulary where practical, but must not assume WP-0200 is already installed.

Because Chief Architect #4 and other workers may be touching Office UI or validation files concurrently, WP-0204 follows the WP-0112 parallel workstream standard. This package stages proposed implementation rather than modifying active Office runtime files directly.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3: WP-0200 through WP-0250.

Do not renumber this package based on GitHub search results.

## Scope
Create staged implementation artifacts for Validation tab controls.

In scope:

1. Inspect current Validation surfaces in the Office implementation.
2. Inspect validation CLI and artifacts, especially `validate-work-package`, `validation-production-readiness`, validation reports, runtime validation JSON, and validation observations.
3. Stage proposed controls for the Validation tab only.
4. Align action metadata with WP-0200 staged action vocabulary where practical.
5. Create staged tests or a test plan.
6. Create `collaboration/workstreams/WP-0204/install_manifest.json`.
7. Create `collaboration/work_packages/completions/WP-0204_codex_done.json`.

## Out of Scope
Do not directly modify active Office runtime files in this package.

Do not declare institutional acceptance from UI state.

Do not bypass Chief Architect review, Steward authority, validation governance, merge authority, or production-readiness policy.

Do not implement controls for Work Packages, Mission Control, Projects, Roadmap, Mailboxes, Parking Lot, Residents, AI Services, Settings, Help, or About except where needed as read-only references.

Do not add cloud services, external API calls, telemetry, or remote workers.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Staging Location
All staged artifacts must live under:

`collaboration/workstreams/WP-0204/`

Expected staged paths may include:

- `collaboration/workstreams/WP-0204/proposed/validation_tab_controls.md`
- `collaboration/workstreams/WP-0204/proposed/action_metadata.json`
- `collaboration/workstreams/WP-0204/proposed/src/estate/core/office_validation_actions.py`
- `collaboration/workstreams/WP-0204/proposed/tests/test_office_validation_actions.py`
- `collaboration/workstreams/WP-0204/install_manifest.json`
- `collaboration/workstreams/WP-0204/validation_notes.md`

## Required Controls to Stage
Stage controls for the Validation tab only.

Proposed controls should include:

1. Open validation report
   - Open/read `operations/validation/reports/*.md` and related runtime JSON.
   - Safe read-only.

2. Copy validation command
   - Copy `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json`.
   - Copy-only by default; do not execute unless a later installed action dispatch layer grants explicit confirmation behavior.

3. Run validation recipe, staged design only
   - Design how the UI would run a validation recipe and show generated artifact paths.
   - Safe local generated-artifact update after explicit confirmation.
   - Must not declare acceptance.

4. Run production readiness, staged design only
   - Design how the UI would run `validation-production-readiness --json` and report output paths.
   - Safe local generated-artifact update after explicit confirmation.
   - Must not override blocker semantics.

5. Inspect blocker/failure detail
   - Drill into source artifacts behind warnings/errors.
   - Safe read-only.

6. Copy failing command
   - Copy command text for the Steward/Codex/local terminal.
   - Safe read-only.

7. Create validation observation draft
   - Draft a validation observation or follow-up note using existing validation observation concepts.
   - Steward-confirmed local mutation.

8. Export validation evidence bundle, staged design only
   - Design export of selected reports/JSON into a local bundle.
   - Safe read-only or generated-artifact update with sensitivity warning.

## Required Action Metadata
For each proposed control, include action metadata with:

- action ID
- label
- target tab
- target validation object or work package ID, when applicable
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
- explicit statement that evidence is not institutional acceptance

Use WP-0118 and WP-0200 vocabulary.

## Required Safety Rules
The staged design must enforce or describe:

1. Validation UI state is evidence, not acceptance.
2. Running a recipe generates evidence and reports output paths.
3. Production readiness output does not bypass blocking semantics.
4. Copy-command controls are safer than execute-command controls.
5. Observation drafting does not close the underlying failure unless routed through approved state transition.
6. Bulk validation or bulk evidence export must summarize affected items and require confirmation.

## Required Install Manifest
Create:

`collaboration/workstreams/WP-0204/install_manifest.json`

The manifest must follow the WP-0112 standard and include staged artifact paths, intended final install paths, expected modified files, manual/automated install steps, validation commands, rollback notes, dependency assumptions, conflict risks, generated artifacts to ignore/review, authority/review requirements, and `staged_work_is_installed: false`.

## Conflict Surface Declaration
Expected conflict surface:

- `src/estate/core/steward_command_center.py` — likely future UI integration target
- `src/estate/core/work_package_validation.py` — possible validation helper reference or future integration target
- `src/estate/core/production_readiness_validation.py` — possible read-only/helper reference
- `src/estate/core/validation_observations.py` — possible observation helper reference
- `src/estate/cli/main.py` — possible command registry reference
- `tests/test_steward_command_center.py` — likely future integration tests
- `tests/test_work_package_validation.py` — possible validation test reference

Risk class: medium/high, because future install likely touches shared Office and validation surfaces.

Packages that can run in parallel:

- Other `PARALLEL-STAGED` tab-control packages that stage under their own workstream directories.

Packages that should complete before install:

- WP-0118 complete and merged.
- WP-0200 reviewed or installed as action framework foundation.
- Any active CA4 validation or Office repair touching these files reviewed for conflicts.

## Required Tests / Staged Tests
Provide staged tests or a test plan proving:

- Open report and inspect blocker are safe read-only.
- Copy validation command is copy-only.
- Run validation and production readiness require confirmation and report output paths.
- Validation result does not imply institutional acceptance.
- Observation draft is a Steward-confirmed local mutation and does not close failures.
- Evidence export includes sensitivity warning.

## Required Validation Commands
Run or document equivalent staged validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0204 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0204 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If WP-0204 has no validation recipe yet because staged packages are not fully integrated into validation, document that limitation in the completion receipt.

## Required Outputs
Create or update:

- `collaboration/workstreams/WP-0204/install_manifest.json`
- staged proposed Validation tab control artifacts under `collaboration/workstreams/WP-0204/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0204_codex_done.json`

Do not install staged files into active runtime paths in this package.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0204_codex_done.json`

It must include work_package_id, codex_status, completed_at, branch, pull_request_url or reason, summary, workstream mode, staged artifact paths, install manifest path, intended install paths, conflict risks, controls staged, files changed, tests/validation run, known limitations, `staged_work_is_installed: false`, `ready_for_ca_review: true`, and `merge_authority: ca_verified_auto_merge_allowed`.

## Acceptance Criteria
WP-0204 is complete when staged Validation tab control artifacts exist, every staged control has action metadata/authority classification/confirmation behavior/local-only posture, no UI state declares acceptance, an install manifest exists, risks are explicit, tests or test plan exist, completion receipt exists, and active Office runtime files are not directly installed.

## Merge Class
Class A if this package only creates staged workstream artifacts, install manifest, tests/test plan, and completion receipt.

Escalate to Class B if active runtime files are modified or the package attempts to install the controls directly.
