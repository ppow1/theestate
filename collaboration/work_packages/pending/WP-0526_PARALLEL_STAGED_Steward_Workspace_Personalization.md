# WP-0526 - Steward Workspace Personalization

## Codex Command
Read collaboration/work_packages/pending/WP-0526_PARALLEL_STAGED_Steward_Workspace_Personalization.md and do exactly what it says.

## Mode
PARALLEL-STAGED

## Mission
Build staged personalization capabilities for saved layouts, pinned items, favorite residents, quick actions, and workspace preferences without altering shared active Office files directly.

## Required Capabilities
- saved workspace layouts;
- pinned projects, work packages, residents, and artifacts;
- favorite actions and quick-launch controls;
- per-workspace visibility and ordering;
- restore defaults and recover from malformed personalization state;
- persistence across reload and restart;
- import/export through safe structured data.

## Staging Requirements
Create under `collaboration/workstreams/WP-0526/`:

```text
install_manifest.json
staged/office_workspace_personalization.py
staged/test_office_workspace_personalization.py
workspace_personalization_contract.md
validation_notes.md
rollback_notes.md
```

Do not modify shared active Office files. WP-0531 performs installation.

## Conflict Surface
Expected final targets include a dedicated personalization module, settings/schema integration, Office rendering hooks, tests, and docs. Declare overlaps with WP-0511 Settings and workspace profiles.

## Validation
Prove save, reload, pin/unpin, order, defaults, malformed-state recovery, and safe import/export.

## Completion Receipt
Create `collaboration/work_packages/completions/WP-0526_codex_done.json` and explicitly state that staged work is not installed work.
