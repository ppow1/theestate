# PARALLEL-STAGED TASK WP-0202 — Work Packages Tab Controls

## Codex Command
Read collaboration/work_packages/pending/WP-0202_PARALLEL_STAGED_work_packages_tab_controls.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Design and stage safe Work Packages tab controls for the Office of the Steward without directly installing changes into active Office runtime files.

This package implements the WP-0118-F2 follow-up slice: Work Packages Tab Controls. It must produce staged, reviewable artifacts under `collaboration/workstreams/WP-0202/`, including proposed UI/control metadata, proposed code or patch structure, tests or staged test plan, validation notes, and an install manifest.

The Work Packages tab should become an operational control surface for inspection, validation, source opening, command copying, review requesting, and batch-manifest submission preparation while explicitly preventing silent execution of pending work packages.

## Background
WP-0118 identified the Work Packages tab as one of the highest-value Office tabs for moving from noun/status display into safe verbs. Current surfaces show package pipeline rows, dependencies, next actions, completion/review state, and source artifacts. The proposed verbs include inspect package, validate package, open pending/completion artifacts, copy commands, request CA review, and submit batch manifest.

WP-0200 stages the shared Office action framework and command-dispatch foundation. WP-0202 should align with that staged action pattern where practical, but it must not assume WP-0200 has already been installed into active runtime files.

Because Chief Architect #4 and other workers may be touching the Office UI at the same time, WP-0202 follows the WP-0112 parallel workstream standard. This package stages proposed implementation rather than modifying active Office runtime files directly.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3:

- WP-0200 through WP-0250

Do not renumber this package based on GitHub search results.

## Scope
Create a staged implementation plan and proposed artifacts for Work Packages tab controls.

In scope:

1. Inspect the current Work Packages and Projects surfaces in the Office implementation.
2. Inspect existing work package validation, assignment queue, handoff, range, and batch-related CLI surfaces.
3. Stage proposed controls for the Work Packages tab only.
4. Use or align with the WP-0200 staged action framework pattern if available.
5. Create staged UI/action metadata for the new controls.
6. Create staged tests or a test plan.
7. Create an install manifest.
8. Create a WP-0202 completion receipt.

## Out of Scope
Do not directly modify active Office runtime files in this package.

Do not install Work Packages tab controls into `src/estate/core/steward_command_center.py` as part of this package.

Do not execute pending work packages.

Do not create autonomous work package execution.

Do not merge pull requests, approve reviews, or mark Chief Architect review as complete.

Do not change canonical work package lifecycle states.

Do not mutate assignment authority or governance authority.

Do not implement controls for Validation, Mailboxes, Parking Lot, Residents, AI Services, Mission Control, Settings, Help, or About except where needed as read-only references.

Do not add cloud services, external API calls, telemetry, or remote workers.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Staging Location
All staged implementation artifacts must live under:

`collaboration/workstreams/WP-0202/`

Expected staged paths may include:

- `collaboration/workstreams/WP-0202/proposed/work_packages_tab_controls.md`
- `collaboration/workstreams/WP-0202/proposed/action_metadata.json`
- `collaboration/workstreams/WP-0202/proposed/src/estate/core/office_work_package_actions.py`
- `collaboration/workstreams/WP-0202/proposed/tests/test_office_work_package_actions.py`
- `collaboration/workstreams/WP-0202/install_manifest.json`
- `collaboration/workstreams/WP-0202/validation_notes.md`

Use the structure that best fits the staged work, but keep all implementation artifacts isolated.

## Required Controls to Stage
Stage controls for the Work Packages tab.

Proposed controls should include safe actions such as:

1. Inspect work package
   - Open/read pending package artifact.
   - Open/read completion receipt where present.
   - Open/read validation report where present.
   - Safe read-only.

2. Open source artifact
   - Expose source paths already known to the pipeline.
   - Safe read-only.

3. Copy Codex command
   - Copy the one-line command for a pending package.
   - Do not execute it.
   - Safe read-only.

4. Copy validation command
   - Example: `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-XXXX --json`.
   - Do not execute unless later explicitly allowed by an installed action framework and confirmation path.
   - Safe read-only.

5. Run validation recipe, staged design only
   - Design how the UI would run validation and show artifact outputs.
   - Treat as safe local generated-artifact update only after explicit confirmation.
   - Distinguish validation evidence from institutional acceptance.

6. Request Chief Architect review
   - Draft or queue a review request through the existing authority path.
   - Do not mark review complete.
   - Authority-gated institutional action.

7. Create blocker note
   - Draft or stage local blocker note tied to a work package.
   - Steward-confirmed local mutation.

8. Prepare sequential batch manifest
   - Draft a batch manifest from explicitly selected packages.
   - Do not execute the batch.
   - Require validation of dependencies and ordering.
   - Authority-gated for submission/execution.

9. Inspect parallel workstream manifest
   - For packages using WP-0112 staged mode, inspect `collaboration/workstreams/WP-XXXX/install_manifest.json`.
   - Safe read-only.

## Required Action Metadata
For each proposed control, include action metadata with at least:

- action ID
- label
- target tab
- target work package ID, when applicable
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
- why the action does not execute pending work packages

Use WP-0118 and WP-0200 vocabulary.

## Required Safety Rules
The staged design must enforce or clearly describe these safety rules:

1. Buttons must not silently execute pending work packages.
2. Copy-command controls must be visually distinct from execute-command controls.
3. Validation evidence must not be displayed as institutional acceptance.
4. CA review request must not be displayed as CA approval.
5. Batch manifest preparation must not submit or execute a batch without explicit later authority.
6. Local blocker notes must not alter canonical work package status unless routed through an approved state transition.
7. Parallel-staged workstream inspection must not install staged work.

## Required Install Manifest
Create:

`collaboration/workstreams/WP-0202/install_manifest.json`

It must follow the WP-0112 standard and include at least:

- `work_package_id`: `WP-0202`
- `workstream_mode`: `PARALLEL-STAGED`
- staged artifact paths
- intended final install paths
- files expected to be modified during install
- manual install steps
- automated install steps, if any
- validation commands
- rollback notes
- dependency assumptions
- conflict risks
- generated artifacts to ignore or review
- authority and review requirements
- `staged_work_is_installed`: `false`

## Conflict Surface Declaration
Expected conflict surface:

- `src/estate/core/steward_command_center.py` — likely future UI integration target
- `src/estate/core/work_package_validation.py` — possible validation helper reference or future integration target
- `src/estate/core/assignment_queue.py` — possible read-only source reference
- `src/estate/core/work_package_handoff.py` — possible read-only source reference
- `src/estate/cli/main.py` — possible command registry reference
- `tests/test_steward_command_center.py` — likely future integration tests
- `tests/test_work_package_validation.py` — possible validation test reference
- `docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md` — reference only
- `docs/templates/Office_Action_Surface_Work_Package_Template.md` — reference only

Risk class: medium/high, because future install likely touches the shared Office command-center implementation and work package validation surfaces.

Packages that can run in parallel:

- WP-0200 staged foundation work.
- WP-0201 staged Settings/Help/About controls.
- Other `PARALLEL-STAGED` tab-control packages that stage work under their own workstream directories.

Packages that should complete before install:

- WP-0118 must be complete and merged.
- WP-0200 should be reviewed before installing WP-0202, because this package should align with the action framework foundation.
- Any active Chief Architect #4 repair touching the Office UI or work package validation should be reviewed for file conflicts before install.

## Required Tests / Staged Tests
Provide staged tests or a test plan proving:

- Work package inspect action is represented as safe read-only.
- Copy Codex command action is represented as copy-only, not executable.
- Copy validation command action is represented as copy-only unless explicitly confirmed in a future dispatch layer.
- Validation run action requires generated-artifact confirmation and reports output paths.
- Review request action is authority-gated and does not mark review complete.
- Batch manifest preparation does not execute selected packages.
- Parallel workstream inspect does not install staged work.

If executable staged tests are included, document how to run them after install.

## Required Validation Commands
Run or document equivalent staged validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0202 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0202 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If WP-0202 has no validation recipe yet because staged packages are not fully integrated into validation, document that limitation and include a follow-up validation recommendation in the completion receipt.

## Required Outputs
Create or update:

- `collaboration/workstreams/WP-0202/install_manifest.json`
- staged proposed Work Packages tab control artifacts under `collaboration/workstreams/WP-0202/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0202_codex_done.json`

Do not install staged files into active runtime paths in this package.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0202_codex_done.json`

It must include:

- `work_package_id = WP-0202`
- `codex_status`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- workstream mode
- staged artifact paths
- install manifest path
- intended install paths
- conflict risks
- controls staged
- files changed
- tests run or staged test plan
- validation commands run
- known limitations
- `staged_work_is_installed = false`
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria
WP-0202 is complete when:

1. Staged Work Packages tab control designs/artifacts exist under `collaboration/workstreams/WP-0202/`.
2. Each staged control has action metadata, authority classification, confirmation behavior, and local-only/no-upload posture.
3. The staged controls explicitly prevent silent work package execution.
4. The staged controls distinguish validation evidence from acceptance and review requests from approvals.
5. An install manifest exists and declares staged work is not installed.
6. Conflict risks and intended final install paths are explicit.
7. Tests or staged test plan exist.
8. Completion receipt exists.
9. The package does not directly install active Office runtime changes.

## Merge Class
Class A if this package only creates staged workstream artifacts, install manifest, tests/test plan, and completion receipt.

Escalate to Class B if active runtime files are modified or the package attempts to install the controls directly.
