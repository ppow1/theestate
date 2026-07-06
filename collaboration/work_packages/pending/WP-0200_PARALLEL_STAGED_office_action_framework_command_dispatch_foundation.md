# PARALLEL-STAGED TASK WP-0200 — Office Action Framework / Command Dispatch Foundation

## Codex Command
Read collaboration/work_packages/pending/WP-0200_PARALLEL_STAGED_office_action_framework_command_dispatch_foundation.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Design and stage the Office of the Steward action framework and command-dispatch foundation without directly installing changes into the active Office runtime files.

This package implements the first follow-up slice from WP-0118: Office Action Framework / Command Dispatch Foundation. It must produce a staged, reviewable implementation package under `collaboration/workstreams/WP-0200/` with an install manifest, proposed code/artifact changes, tests, validation notes, and a clear integration plan.

The staged work must enable future Office tabs to move from noun/status views into safe verb/action surfaces while preserving Steward authority, Chief Architect review, validation boundaries, and local-first operation.

## Background
WP-0118 identified that the Office of the Steward is currently mostly nouns and status surfaces. It inventories tabs/workspaces and recommends implementation slices F1 through F9.

WP-0200 corresponds to WP-0118-F1:

Office Action Framework / Command Dispatch Foundation — Define an Office action registry, action metadata schema, allowlisted local command hooks, common confirmation model, output-path reporting, and test fixtures without implementing high-risk controls.

The Estate is now operating with multiple architects and multiple Codex workers. To avoid stepping on active work by Chief Architect #4 or other workers, this package must follow the WP-0112 parallel workstream standard. That means the implementation happens in a staged workstream directory and is not installed into active runtime files until a later install-handoff package or explicit reviewer-directed handoff.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3:

- WP-0200 through WP-0250

Do not renumber this package based on GitHub search results.

## Scope
Create a staged action framework foundation for the Office of the Steward.

In scope:

1. Inspect the current Office implementation, especially:
   - `src/estate/core/steward_command_center.py`
   - `src/estate/cli/main.py`
   - existing Office settings/profile modules
   - existing tests for the command center
   - WP-0118 backlog and template documents
2. Design a minimal Office action registry model.
3. Define action metadata fields.
4. Define safe action categories and authority classes.
5. Define a common confirmation model.
6. Define output-path reporting for generated artifacts and local mutations.
7. Define local-only command hook shape for future registered commands.
8. Provide staged implementation files or patch proposals under `collaboration/workstreams/WP-0200/`.
9. Provide tests or staged test proposals for the action registry.
10. Create `collaboration/workstreams/WP-0200/install_manifest.json`.
11. Create a WP-0200 completion receipt.

## Out of Scope
Do not directly modify active runtime implementation files outside the staged workstream unless the package explicitly determines that a documentation-only update is safe and records that decision in the install manifest.

Do not install the Office action framework into `src/estate/core/steward_command_center.py` as part of this package.

Do not implement tab-specific controls for Work Packages, Validation, Mailboxes, Parking Lot, Residents, AI Services, or Mission Control. Those belong to later packages.

Do not add destructive controls.

Do not add autonomous pending work package execution.

Do not let the UI bypass Steward authority, Chief Architect review, validation, governance, resident authority boundaries, or merge authority.

Do not add cloud calls, external services, telemetry, or network dependencies.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Staging Location
All staged implementation artifacts must live under:

`collaboration/workstreams/WP-0200/`

Expected staged paths may include:

- `collaboration/workstreams/WP-0200/proposed/src/estate/core/office_actions.py`
- `collaboration/workstreams/WP-0200/proposed/tests/test_office_actions.py`
- `collaboration/workstreams/WP-0200/proposed/docs/office_action_registry_notes.md`
- `collaboration/workstreams/WP-0200/install_manifest.json`
- `collaboration/workstreams/WP-0200/validation_notes.md`

Use the exact structure that best fits existing repository conventions, but keep staged work isolated.

## Required Action Registry Design
The staged framework must define or propose an action registry capable of describing future Office controls.

Each action should be able to declare at least:

- action ID
- label
- target tab/workspace
- description
- action class
- authority/safety class
- confirmation requirement
- local-only status
- reads artifacts
- writes artifacts
- command hook or handler reference
- expected output paths
- validation command, if applicable
- failure behavior
- audit/logging expectation
- disabled/prohibited reason, if not currently available

Use WP-0118's action classes and safety classes as the base vocabulary.

## Required Authority Classes
Support at least the WP-0118 authority classes:

1. Safe read-only
2. Safe local generated-artifact update
3. Steward-confirmed local mutation
4. Authority-gated institutional action
5. Prohibited until future governance/tooling exists

The staged framework must make it difficult to accidentally treat an authority-gated action as a safe read-only action.

## Required Confirmation Model
Define a common confirmation model for future actions.

At minimum, the confirmation model should support:

- no confirmation required for safe read-only actions
- confirmation required for generated artifact updates
- preview-before-write for local mutations
- explicit authority route for authority-gated actions
- unavailable/prohibited actions omitted or clearly unavailable with reason
- bulk action summary before execution

## Required Command Hook Model
Define a minimal local command hook shape for future actions.

The model should record:

- command text or handler ID
- whether the command is copy-only or executable
- whether execution is currently allowed
- expected outputs
- working directory assumptions
- environment assumptions such as `PYTHONPATH=src`
- timeout/failure handling notes

Default posture: copy-command is safer than execute-command. Direct execution must require explicit future package authority.

## Required Install Manifest
Create:

`collaboration/workstreams/WP-0200/install_manifest.json`

It must follow the WP-0112 standard and include at least:

- `work_package_id`: `WP-0200`
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

- `src/estate/core/steward_command_center.py` — likely future integration target for action rendering/dispatch
- `src/estate/cli/main.py` — possible future integration if action registry inspection CLI is added
- `tests/test_steward_command_center.py` — possible future integration tests
- `tests/test_office_actions.py` — likely new test file during install
- `src/estate/core/office_actions.py` — likely new module during install
- `docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md` — reference only, avoid modifying unless necessary
- `docs/templates/Office_Action_Surface_Work_Package_Template.md` — reference only, avoid modifying unless necessary

Risk class: medium, because future install likely touches the shared Office command-center implementation.

Packages that can run in parallel:

- Documentation-only planning packages that do not modify Office runtime files.
- Other `PARALLEL-STAGED` Office tab-control packages that stage work under their own workstream directories.

Packages that should complete before install:

- WP-0118 must be complete and merged.
- Any active Chief Architect #4 repair touching the Office UI should be reviewed for file conflicts before install.

## Required Tests / Staged Tests
Provide staged tests or a test plan proving the action framework can represent:

- safe read-only action
- safe generated-artifact update
- Steward-confirmed local mutation
- authority-gated institutional action
- prohibited/unavailable action
- copy-command action
- output-path reporting
- confirmation requirement

If executable staged tests are included, document how to run them after install.

## Required Validation Commands
Run or document equivalent staged validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0200 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0200 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If WP-0200 has no validation recipe yet because staged packages are not fully integrated into validation, document that limitation and include a follow-up validation recommendation in the completion receipt.

## Required Outputs
Create or update:

- `collaboration/workstreams/WP-0200/install_manifest.json`
- staged proposed action framework artifacts under `collaboration/workstreams/WP-0200/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0200_codex_done.json`

Do not install staged files into active runtime paths in this package.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0200_codex_done.json`

It must include:

- `work_package_id = WP-0200`
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
- files changed
- tests run or staged test plan
- validation commands run
- known limitations
- `staged_work_is_installed = false`
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria
WP-0200 is complete when:

1. A staged Office action framework design/implementation exists under `collaboration/workstreams/WP-0200/`.
2. The staged framework defines action metadata, authority classes, confirmation behavior, command hooks, and output-path reporting.
3. An install manifest exists and declares staged work is not installed.
4. Conflict risks and intended final install paths are explicit.
5. Tests or staged test plan exist.
6. Completion receipt exists.
7. The package does not directly install active Office runtime changes.

## Merge Class
Class A if this package only creates staged workstream artifacts, install manifest, tests/test plan, and completion receipt.

Escalate to Class B if active runtime files are modified or the package attempts to install the action framework directly.
