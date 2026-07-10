# WP-4030 — Estate Backup, Restore, and Resident Continuity Recovery

Status: Pending
Workstream Mode: PARALLEL-INDEPENDENT
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Classification: Estate Internal

## Objective

Implement an isolated local backup and restore service for resident and institutional records created by the resident-runtime workstream.

## Conflict Surface

Primary implementation must remain isolated. Intended later integrations include CLI registration, Office status, service supervision, and lifecycle reporting.

Conflict risk: low during development; medium during install.

## Staged Paths

Use only `collaboration/workstreams/WP-4030/` for source, schemas, tests, fixtures, restore drills, integration notes, and `install_manifest.json`.

## Required Implementation

Stage:

- backup scope definitions;
- manifest creation;
- checksums and integrity verification;
- incremental and full backup plans;
- resident identity, continuity, journal, mail, session, task, lifecycle, knowledge metadata, and configuration coverage;
- selective restore;
- dry-run restore;
- collision and overwrite protection;
- disaster-recovery rehearsal;
- backup retention metadata;
- large-model and generated-output exclusion/reference handling;
- truthful partial-failure reporting.

## Boundaries

Do not silently back up unrestricted external paths, secrets, caches, large model binaries, or protected material outside declared scope. Do not overwrite active records without explicit restore approval. Do not create cloud storage.

## Acceptance Criteria

- backup manifests are deterministic and source-linked;
- integrity verification detects corruption or missing files;
- selective restore works in an isolated test root;
- dry-run reports collisions before writing;
- large models are inventoried by reference unless explicitly included;
- staged tests pass;
- manifest remains uninstalled.

## Required Install Handoff

WP-4031 installs approved CLI, Office, and service-status integrations after staged validation.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4030_Estate_Backup_Restore_and_Resident_Continuity_Recovery.md and do exactly what it says.
```
