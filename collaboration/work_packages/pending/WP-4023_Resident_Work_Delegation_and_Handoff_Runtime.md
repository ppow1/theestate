# WP-4023 — Resident Work Delegation and Handoff Runtime

Status: Pending
Workstream Mode: PARALLEL-STAGED
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Stage a governed delegation and handoff runtime for residents, departments, and Dispatch without modifying shared assignment, CLI, Dispatch, or Office files during this package.

## Conflict Surface

Expected integration targets:

- assignment and work-package runtime modules;
- Dispatch and Traffic Controller integration points;
- `src/estate/cli/main.py`;
- Office task and resident surfaces.

Conflict risk: high.

## Staged Paths

Use only:

```text
collaboration/workstreams/WP-4023/
```

Create isolated source, tests, integration notes, and `install_manifest.json`. Do not edit active shared files.

## Required Implementation

Stage contracts and local behavior for:

- delegation request;
- recipient acceptance or decline;
- ownership transfer;
- prerequisites and evidence;
- completion criteria;
- handoff receipt;
- stalled, rejected, returned, and completed states;
- idempotent retry;
- source authority and approval metadata.

Reuse existing assignment, Traffic Controller, work-package, Dispatch, mailbox, and audit mechanisms.

## Boundaries

Do not create a second queue, assignment registry, Dispatch path, or authority layer. A delegated message does not itself grant authority.

## Acceptance Criteria

- delegation states are deterministic;
- ownership cannot change without an authorized transition;
- rejected and stalled work remains visible;
- receipts preserve evidence and provenance;
- staged tests pass;
- manifest is complete with `staged_work_is_installed: false`.

## Required Install Handoff

WP-4031 performs shared-file integration.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4023_Resident_Work_Delegation_and_Handoff_Runtime.md and do exactly what it says.
```
