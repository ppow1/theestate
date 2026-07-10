# WP-0531 - Office Intelligence Wave Installation and Acceptance

## Codex Command
Read collaboration/work_packages/pending/WP-0531_INSTALL_HANDOFF_Office_Intelligence_Wave_Installation_and_Acceptance.md and do exactly what it says.

## Mode
INSTALL-HANDOFF

## Mission
Inspect, conflict-review, install, validate, and operationally accept the staged Office intelligence workstreams from WP-0522 through WP-0530 as one controlled installation program.

This package is the only package in this wave authorized to integrate staged work into shared active Office files.

## Source Workstreams

```text
collaboration/workstreams/WP-0522/
collaboration/workstreams/WP-0523/
collaboration/workstreams/WP-0524/
collaboration/workstreams/WP-0525/
collaboration/workstreams/WP-0526/
collaboration/workstreams/WP-0527/
collaboration/workstreams/WP-0528/
collaboration/workstreams/WP-0529/
collaboration/workstreams/WP-0530/
```

## Preconditions
For each workstream, inspect:

- `install_manifest.json`;
- completion receipt;
- staged source and tests;
- validation notes;
- rollback notes;
- dependency assumptions;
- intended final install paths;
- shared-file conflict declarations.

Missing or invalid workstreams must remain staged and be marked blocked. Do not fabricate artifacts.

## Required Workstream Directory
Create:

```text
collaboration/workstreams/WP-0531/
```

Required artifacts:

```text
install_manifest.json
office_intelligence_install_plan.json
office_intelligence_conflict_matrix.json
office_intelligence_install_execution_report.md
office_intelligence_rollback_plan.md
post_install_validation.md
operational_acceptance_report.md
remaining_defects.json
```

## Required Install Process

1. Validate every available source manifest.
2. Build a file-level conflict matrix.
3. Detect duplicate runtimes, action IDs, schemas, routes, tab IDs, and UI components.
4. Normalize all workstreams to one Office action transport and one set of shared contracts.
5. Determine a safe phased install order.
6. Install only phases that are complete, compatible, rollback-ready, and testable.
7. Run focused tests after each phase.
8. Run the full Office regression suite after all installed phases.
9. Leave incompatible or incomplete work staged with explicit reasons.
10. Produce an operational acceptance report and narrow remaining-defect inventory.

## Recommended Install Phases

```text
Phase 1 - shared guided-action contracts: WP-0523
Phase 2 - personalization and unified search: WP-0526, WP-0527
Phase 3 - timeline, presence, and notifications: WP-0524, WP-0525, WP-0528
Phase 4 - executive workspace and decision support: WP-0522, WP-0529
Phase 5 - guided operational workflows: WP-0530
Phase 6 - integrated Office regression and acceptance
```

Change the order when the manifests and actual conflicts require it. Document every deviation.

## Shared Hot Files
Treat at minimum these as controlled integration targets:

```text
src/estate/core/steward_command_center.py
src/estate/core/office_command_surface.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
src/estate/core/operations_center_settings.py
```

Do not blindly overwrite any shared file. Integrate semantically and preserve existing functionality from WP-0510 through WP-0521.

## Acceptance Tests
Prove end-to-end browser-to-handler-to-state-to-render behavior for:

- executive attention and readiness;
- guided cross-Office action;
- actionable notification follow-up;
- resident presence drill-down;
- saved personalization;
- unified search and safe command invocation;
- operational timeline;
- decision support;
- guided operational workflow;
- reload/restart persistence;
- failure recovery and diagnostics.

Use fake providers and service runners. Do not make live provider calls during deterministic validation.

## Authority Boundaries

- recommendations are evidence, not decisions;
- guided workflows do not manufacture authorization;
- validation evidence is not institutional acceptance;
- no automatic approval, retry, merge, provider selection, or acceptance;
- no arbitrary shell or handler execution;
- staged work is not installed until this handoff installs and validates it.

## Completion Receipt
Create:

```text
collaboration/work_packages/completions/WP-0531_codex_done.json
```

It must identify every source workstream as installed, partially installed, blocked, or not present; list active files changed; record phase-by-phase validation; include rollback instructions; and state whether the Office intelligence wave is ready for Chief Architect and Steward review.

## Acceptance Criteria

1. Every available manifest is validated.
2. A complete conflict matrix and install plan exist.
3. Shared files are modified only through this install handoff.
4. Installed workstreams use one command transport and compatible contracts.
5. Focused and full regression tests pass for installed phases.
6. Blocked work remains staged with explicit reasons.
7. Rollback is documented and practical.
8. Operational acceptance is evidence for Steward review, not automatic institutional acceptance.
