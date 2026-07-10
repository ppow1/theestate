# WP-4022 — Resident Capability and Tool Access Integration

Status: Pending
Workstream Mode: PARALLEL-STAGED
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Implement resident-specific capability and tool-access resolution without editing shared active runtime files during the staged workstream.

## Conflict Surface

Expected integration targets:

- `src/estate/core/resident_interaction.py`
- `src/estate/core/resident_authority.py`
- `src/estate/cli/main.py`
- Office resident/status surfaces

Conflict risk: high.

## Staged Paths

All implementation work must remain under:

```text
collaboration/workstreams/WP-4022/
```

Create isolated source, tests, integration notes, and:

```text
collaboration/workstreams/WP-4022/install_manifest.json
```

Do not modify active integration targets in this package.

## Required Implementation

Stage:

- resident-specific capability resolution;
- approved tool and connector access checks;
- runtime availability reporting;
- approval-required operation metadata;
- truthful unavailable and denied states;
- capability display payloads for resident and Office surfaces;
- tests for Alfred, Helen, Grace candidate, and unknown residents.

Reuse existing authority, resident surface, model-control, connector, and Office systems.

## Install Manifest Requirements

Declare staged artifacts, intended install paths, files expected to change, install steps, validation, rollback, dependencies, conflict risks, generated artifacts, and review requirements. Set `staged_work_is_installed` to `false`.

## Acceptance Criteria

- staged implementation is isolated;
- capability resolution is deterministic;
- no resident silently gains undeclared access;
- unavailable tools are reported truthfully;
- install manifest is complete;
- focused staged tests pass.

## Required Install Handoff

WP-4031 installs this work after conflict review.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4022_Resident_Capability_and_Tool_Access_Integration.md and do exactly what it says.
```
