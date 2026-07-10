# WP-4024 — Resident Context Assembly and Retrieval Pipeline

Status: Pending
Workstream Mode: PARALLEL-STAGED
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Stage a shared context-assembly pipeline that supplies each resident with the minimum relevant Estate context for a conversation or task.

## Conflict Surface

Expected integration targets:

- resident interaction and prompt construction;
- knowledge retrieval;
- continuity and session stores;
- classification filtering;
- Office resident surfaces.

Conflict risk: high.

## Staged Paths

Use only `collaboration/workstreams/WP-4024/` for implementation, tests, integration notes, fixtures, and `install_manifest.json`.

## Required Implementation

Stage context assembly for:

- canonical resident profile;
- office and role state;
- current task and blockers;
- recent relevant communications;
- approved continuity artifacts;
- knowledge-index retrieval;
- source citations;
- classification filtering;
- stale-context warnings;
- deterministic context-size budgeting;
- explicit omitted-source reasons.

The assembler must consume existing sources. It must not become a second memory store.

## Boundaries

Do not ingest unrestricted journals, protected private character material, or unrelated records. Do not silently truncate without metadata. Do not fabricate unavailable context.

## Acceptance Criteria

- context is resident-specific, relevant, source-linked, and bounded;
- privacy filtering is enforced before prompt assembly;
- stale and unavailable sources are labeled;
- token/character budgeting is deterministic;
- staged tests pass;
- manifest declares all intended shared-file integrations and remains uninstalled.

## Required Install Handoff

WP-4031 integrates this pipeline into active resident chat and task execution.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4024_Resident_Context_Assembly_and_Retrieval_Pipeline.md and do exactly what it says.
```
