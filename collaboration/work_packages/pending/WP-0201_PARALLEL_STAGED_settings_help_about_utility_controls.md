# PARALLEL-STAGED TASK WP-0201 — Settings, Help, About Utility Controls

## Codex Command
Read collaboration/work_packages/pending/WP-0201_PARALLEL_STAGED_settings_help_about_utility_controls.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Design and stage the first low-risk Office utility controls for Settings, Help, and About without directly installing changes into active Office runtime files.

This package implements the WP-0118-F9 follow-up slice: Settings, Help, About Utility Controls. It must produce staged, reviewable implementation artifacts under `collaboration/workstreams/WP-0201/`, including proposed code/UI changes, tests or staged test plan, and an install manifest.

The purpose is to make the safest Office tabs more useful as controls before implementing higher-risk operational tabs.

## Background
WP-0118 identified that the Office of the Steward is currently mostly a noun/status surface. It recommended a series of action/control implementation slices. The safest immediate implementation slice after the action framework foundation is Settings, Help, and About because these tabs primarily involve local preferences, documentation guidance, diagnostics export, version/source inspection, and support bundle affordances.

WP-0200 stages the shared Office action framework and command-dispatch foundation. WP-0201 should depend on that staged pattern where practical, but it must not assume WP-0200 has already been installed into active runtime files.

Because Chief Architect #4 and other workers may be touching the Office UI at the same time, WP-0201 follows the WP-0112 parallel workstream standard. This package stages proposed implementation rather than modifying active Office runtime files directly.

## Number Allocation
This package uses the temporary active authoring block assigned by the Steward to Chief Architect #3:

- WP-0200 through WP-0250

Do not renumber this package based on GitHub search results.

## Scope
Create a staged implementation plan and proposed artifacts for Settings, Help, and About utility controls.

In scope:

1. Inspect current Settings, Help, and About surfaces in the Office implementation.
2. Identify the current noun/status content for those tabs.
3. Stage proposed utility controls for those tabs.
4. Use or align with the WP-0200 staged action framework pattern if available.
5. Create staged UI/action metadata for the new controls.
6. Create staged tests or a test plan.
7. Create an install manifest.
8. Create a WP-0201 completion receipt.

## Out of Scope
Do not directly modify active Office runtime files in this package.

Do not install Settings, Help, or About controls into `src/estate/core/steward_command_center.py` as part of this package.

Do not implement controls for Work Packages, Validation, Mailboxes, Notifications, Parking Lot, Residents, AI Services, Mission Control, Projects, or Roadmap.

Do not store secrets.

Do not implement import of settings from untrusted files.

Do not perform destructive settings reset without confirmation design.

Do not add cloud services, external API calls, telemetry, or remote diagnostics uploads.

Do not change Steward, Chief Architect, Resident, governance, validation, production-readiness, or merge authority.

Do not edit `estate_ledger/ledger.md` or `development/devlog.md` unless current repository standards require it.

## Required Staging Location
All staged implementation artifacts must live under:

`collaboration/workstreams/WP-0201/`

Expected staged paths may include:

- `collaboration/workstreams/WP-0201/proposed/settings_help_about_controls.md`
- `collaboration/workstreams/WP-0201/proposed/action_metadata.json`
- `collaboration/workstreams/WP-0201/proposed/src/estate/core/office_settings_help_about_actions.py`
- `collaboration/workstreams/WP-0201/proposed/tests/test_office_settings_help_about_actions.py`
- `collaboration/workstreams/WP-0201/install_manifest.json`
- `collaboration/workstreams/WP-0201/validation_notes.md`

Use the structure that best fits the staged work, but keep all implementation artifacts isolated.

## Required Controls to Stage
Stage controls for these tabs only.

### Settings
Proposed controls should include safe local utility actions such as:

- inspect current local settings payload
- export local settings/profile snapshot
- draft or preview reset-to-default action
- save active tab or workspace profile, if already supported by existing settings manager
- copy local settings command, if one exists
- show settings source artifact paths

Settings controls must distinguish between read-only inspection, local preference mutation, and any future authority-gated configuration changes.

### Help
Proposed controls should include safe documentation utility actions such as:

- open local documentation links
- copy support/debug command
- export help/document index snapshot
- draft documentation feedback note
- link to Office action-surface template and verb-surface backlog
- show local-only support bundle guidance

Help must explain authority boundaries; it must not override them.

### About
Proposed controls should include safe diagnostic actions such as:

- copy version manifest
- export diagnostics manifest
- inspect component/source artifact inventory
- compare generated/runtime version metadata, if existing data supports it
- link to snapshot export feature
- show known limitations and source paths

Diagnostics may include internal paths and operational state, so staged design must include a sensitivity warning.

## Required Action Metadata
For each proposed control, include action metadata with at least:

- action ID
- label
- target tab
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

Use WP-0118 and WP-0200 vocabulary.

## Required Install Manifest
Create:

`collaboration/workstreams/WP-0201/install_manifest.json`

It must follow the WP-0112 standard and include at least:

- `work_package_id`: `WP-0201`
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
- `src/estate/core/operations_center_settings.py` — possible settings helper reference or future integration target
- `src/estate/core/operations_center_workspace_profiles.py` — possible profile helper reference or future integration target
- `tests/test_steward_command_center.py` — likely future integration tests
- `tests/test_operations_center_settings.py` if it exists, otherwise possible new tests during install
- `docs/operations/Office_of_the_Steward_Verb_Surface_Control_Backlog_v1.md` — reference only
- `docs/templates/Office_Action_Surface_Work_Package_Template.md` — reference only

Risk class: medium, because future install likely touches the shared Office command-center implementation.

Packages that can run in parallel:

- WP-0200 as staged foundation work.
- Other `PARALLEL-STAGED` tab-control packages that stage work under their own workstream directories.

Packages that should complete before install:

- WP-0118 must be complete and merged.
- WP-0200 should be reviewed before installing WP-0201, because this package should align with the action framework foundation.
- Any active Chief Architect #4 repair touching the Office UI should be reviewed for file conflicts before install.

## Required Tests / Staged Tests
Provide staged tests or a test plan proving:

- Settings controls are represented with correct action metadata.
- Help controls are represented with correct action metadata.
- About controls are represented with correct action metadata.
- Local-only/no-upload rule is represented.
- Mutating settings controls require preview/confirmation.
- Diagnostics export includes sensitivity warning.
- No destructive action is allowed without explicit future design.

If executable staged tests are included, document how to run them after install.

## Required Validation Commands
Run or document equivalent staged validation:

```bash
PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0201 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0201 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If WP-0201 has no validation recipe yet because staged packages are not fully integrated into validation, document that limitation and include a follow-up validation recommendation in the completion receipt.

## Required Outputs
Create or update:

- `collaboration/workstreams/WP-0201/install_manifest.json`
- staged proposed Settings/Help/About utility control artifacts under `collaboration/workstreams/WP-0201/`
- staged tests or test plan
- `collaboration/work_packages/completions/WP-0201_codex_done.json`

Do not install staged files into active runtime paths in this package.

## Completion Artifact
Create:

`collaboration/work_packages/completions/WP-0201_codex_done.json`

It must include:

- `work_package_id = WP-0201`
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
- controls staged by tab
- files changed
- tests run or staged test plan
- validation commands run
- known limitations
- `staged_work_is_installed = false`
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria
WP-0201 is complete when:

1. Staged Settings, Help, and About control designs/artifacts exist under `collaboration/workstreams/WP-0201/`.
2. Each staged control has action metadata, authority classification, confirmation behavior, and local-only/no-upload posture.
3. The staged controls avoid destructive or authority-changing behavior.
4. An install manifest exists and declares staged work is not installed.
5. Conflict risks and intended final install paths are explicit.
6. Tests or staged test plan exist.
7. Completion receipt exists.
8. The package does not directly install active Office runtime changes.

## Merge Class
Class A if this package only creates staged workstream artifacts, install manifest, tests/test plan, and completion receipt.

Escalate to Class B if active runtime files are modified or the package attempts to install the controls directly.
