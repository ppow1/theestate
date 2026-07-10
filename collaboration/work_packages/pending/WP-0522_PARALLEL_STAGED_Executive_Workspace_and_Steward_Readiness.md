# WP-0522 - Executive Workspace and Steward Readiness

## Codex Command
Read collaboration/work_packages/pending/WP-0522_PARALLEL_STAGED_Executive_Workspace_and_Steward_Readiness.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Build an executive workspace that answers what requires the Steward's attention now and whether the Estate is safe to leave unattended, without editing shared active Office files directly.

## Required Capabilities
- prioritized attention queue assembled from existing Estate evidence;
- current blockers, stale work, failed validation, provider/runtime health, unresolved decisions, and pending reviews;
- recommended next governed action with explanation and evidence links;
- readiness verdict for short unattended operation;
- drill-down into source artifacts and controlling workspaces;
- truthful uncertainty and missing-evidence handling.

Recommendations are evidence, not decisions.

## Staging Requirements
Create all implementation under:

```text
collaboration/workstreams/WP-0522/
```

Required artifacts:

```text
install_manifest.json
staged/office_executive_workspace.py
staged/test_office_executive_workspace.py
executive_workspace_contract.md
validation_notes.md
rollback_notes.md
```

Do not modify `steward_command_center.py`, `office_command_surface.py`, `cli/main.py`, or other shared active Office files.

## Install Manifest
Declare staged artifacts, intended final install paths, shared integration targets, dependency assumptions, conflict risks, validation commands, rollback, and authority boundaries. Declare WP-0531 as the required INSTALL-HANDOFF.

## Conflict Surface
Expected install targets may include a dedicated executive workspace module, Office tab registration, command-surface registration, tests, and documentation. Shared-file integration is deferred to WP-0531.

## Validation
Prove deterministic attention ranking, readiness verdicts, evidence linking, missing-data behavior, and no autonomous approval or execution.

## Completion Receipt
Create `collaboration/work_packages/completions/WP-0522_codex_done.json` and state that staged work is not installed work.
