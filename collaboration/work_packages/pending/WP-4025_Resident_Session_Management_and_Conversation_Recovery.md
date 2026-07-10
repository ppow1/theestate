# WP-4025 — Resident Session Management and Conversation Recovery

Status: Pending
Workstream Mode: PARALLEL-STAGED
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Stage durable resident session management and conversation recovery across browser restarts, service restarts, and new operational cycles.

## Conflict Surface

Expected integration targets:

- `src/estate/core/resident_interaction.py`;
- resident gateway/session APIs;
- Open WebUI mapping;
- continuity records;
- Office conversation surfaces.

Conflict risk: high.

## Staged Paths

Use only `collaboration/workstreams/WP-4025/` for implementation, tests, migration notes, fixtures, and `install_manifest.json`.

## Required Implementation

Stage:

- session creation, naming, resume, archive, forget, and recovery;
- resident/session identity validation;
- active-cycle linkage;
- conversation checkpoints;
- restart-safe persistence;
- interrupted-write recovery;
- Open WebUI conversation/session mapping;
- deterministic session listing and status;
- compatibility with existing resident chat records.

## Boundaries

Do not create a second conversation store. Do not merge sessions across resident identities. Do not treat archived or forgotten content as active memory. Do not expose private sessions through public Office surfaces.

## Acceptance Criteria

- sessions survive restart and resume correctly;
- resident identity cannot drift across recovery;
- interrupted writes recover safely;
- archive and forget behavior remain distinct and auditable;
- staged tests pass;
- manifest is complete and marks staged work uninstalled.

## Required Install Handoff

WP-4031 installs shared session integrations after conflict review.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4025_Resident_Session_Management_and_Conversation_Recovery.md and do exactly what it says.
```
