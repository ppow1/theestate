# WP-4029 — Resident Files, Attachments, and Working Artifact Exchange

Status: Pending
Workstream Mode: PARALLEL-STAGED
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Stage bounded local file and attachment exchange for resident conversations, mail, delegated work, and Office surfaces.

## Conflict Surface

Expected integration targets:

- resident interaction attachments;
- mailbox and conversation bus;
- delegated task records;
- Office upload and download surfaces;
- `src/estate/cli/main.py`.

Conflict risk: high.

## Staged Paths

Use only `collaboration/workstreams/WP-4029/` for source, schemas, tests, sample files, integration notes, and `install_manifest.json`.

## Required Implementation

Stage:

- attachment intake and metadata;
- deterministic storage paths;
- classification and ownership;
- size, type, and extension validation;
- image and document summary adapters;
- task, message, and session linkage;
- redaction and retention states;
- controlled read, download, export, and archive behavior;
- checksum and duplicate detection;
- bounded Office and Open WebUI compatibility;
- audit events for sensitive access.

Reuse existing attachment storage, vision adapter, mailbox, resident session, classification, and audit mechanisms.

## Boundaries

Do not build a cloud drive, execute uploaded files, expose protected attachments publicly, or treat summaries as source content. Deterministic tests must not require live models.

## Acceptance Criteria

- attachments are source-linked, checksummed, classified, and auditable;
- unsupported or dangerous inputs fail safely;
- summaries remain distinct from originals;
- message, task, and session links are preserved;
- staged tests pass;
- install manifest is complete and uninstalled.

## Required Install Handoff

WP-4031 installs active resident, mail, CLI, and Office integrations.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4029_Resident_Files_Attachments_and_Working_Artifact_Exchange.md and do exactly what it says.
```
