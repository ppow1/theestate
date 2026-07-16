# Estate PTM Dispatch Evidence and Pilot Migration Contract

Status: Draft implementation-preparation artifact for PTM-06 Gate D
Campaign: PTM-06 — Dispatch evidence and pilot migration
Packages: DISPATCH-PTM-001, MIG-PTM-001A, MIG-PTM-001B
Date: 2026-07-16

## Authority and boundaries

This artifact satisfies the PTM-06 bounded deliverables for dispatch evidence and pilot migration planning. It is source-backed by the accepted PTM baseline, the package and campaign manifests, the dependency manifest, the PTM parallel execution plan, the PTM dependency plan, the promoted Pending package files, and the source planning drafts.

This artifact does not authorize production PTM code, does not execute any migration, does not mutate source work packages, and does not create a second dispatch queue, second registry, second scheduler, local-worker route, or new governance authority. Future execution must use the frozen PTM event envelope, command envelope, ID formats, projection envelope, governed intake model, file-import report contract, schedule readiness gate, and validation contracts already established by upstream PTM packages.

## DISPATCH-PTM-001 task-to-dispatch evidence chain

A future dispatch integration may link a canonical PTM task to existing work packages, dispatch attempts, evidence, validation, and acceptance through an evidence-chain record. The record is a projection/validation artifact over canonical PTM events and source artifacts; it is not a dispatch queue and cannot independently authorize work.

```yaml
ptm_dispatch_evidence_chain:
  chain_id: string
  task_ref: object
  project_ref: object | null
  source_work_package_refs: [object]
  dispatch_attempt_refs: [object]
  evidence_refs: [object]
  validation_refs: [object]
  acceptance_refs: [object]
  readiness_gate_ref: object | null
  latest_dispatch_state: not_dispatched | queued_elsewhere | dispatched | in_progress | blocked | completed | accepted | rejected | superseded
  provenance:
    source_paths: [string]
    source_sha256_refs: [object]
    source_event_ids: [string]
  warnings: [string]
```

### Dispatch-linking rules

- `chain_id` must reference the canonical PTM task identifier and may use a deterministic derived identifier; it must not mint a separate task or registry identity.
- `task_ref` must point to a canonical PTM task projection produced from the append-only ledger.
- `source_work_package_refs` preserve existing package paths, statuses, and hashes where available.
- `dispatch_attempt_refs` may reference accepted dispatch artifacts or future Codex handoff artifacts, but they may not become an alternate dispatch queue.
- `evidence_refs`, `validation_refs`, and `acceptance_refs` must remain source-backed and auditable.
- `latest_dispatch_state` is derived from the linked evidence and must surface unknown, blocked, rejected, and superseded conditions without coercion.

### Evidence chain validation

A dispatch evidence chain is valid only when all referenced source artifacts can be resolved by path, event ID, report ID, or explicit external reference. Missing or stale evidence produces warnings and a non-passing validation state rather than silent acceptance.

## MIG-PTM-001A pilot migration source slice plan

The accepted pilot migration slice is the PTM work-package library and campaign-handoff metadata, limited to repository-local PTM planning and work-package artifacts. The slice is small enough to validate manually and representative enough to exercise source provenance, duplicate handling, dispatch linkage, and rollback.

### Pilot slice

| Source group | Included paths | Migration intent |
| --- | --- | --- |
| Package manifests | `collaboration/work_packages/planning/estate_ptm_package_manifest.json`, `collaboration/work_packages/planning/estate_ptm_campaign_manifest.json`, `collaboration/work_packages/planning/estate_ptm_dependency_manifest.json` | Stage manifest-backed portfolio, project, package, dependency, and campaign references. |
| Pending package files | `collaboration/work_packages/pending/*PTM*.md` for the accepted PTM package set | Stage package/task candidates and source status evidence. |
| Campaign handoffs | `collaboration/work_packages/campaigns/ptm/PTM-*.md` and `PTM_EXECUTABLE_CAMPAIGN_HANDOFF_INDEX.md` | Stage campaign grouping, launch order, checkpoints, and validation obligations. |
| Completion receipts | `collaboration/work_packages/completions/*PTM*_completion_receipt.md` | Link validation and acceptance evidence to staged packages. |

### Source mapping

```yaml
ptm_pilot_migration_source_map:
  migration_slice_id: ptm_work_package_library_v1
  source_ref:
    source_path: string
    source_sha256: string
    parser_format: markdown_work_package | json_manifest
  proposed_record_type: portfolio | project | task | dependency | campaign | evidence
  proposed_record_id: string | null
  canonical_source_contract: file_import_report | governed_intake_candidate | dispatch_evidence_chain
  duplicate_policy: retain_existing | mark_duplicate | supersede_with_review | reject
  rollback_action: discard_staged_candidate | append_compensating_event | retain_source_only
  warnings: [string]
```

### Duplicate policy

- Manifest IDs are authoritative for duplicate detection when present.
- Markdown package titles and declared package IDs must be normalized and compared against manifest membership.
- Completion receipts are evidence records linked to existing package/task candidates, not new tasks.
- Campaign handoffs are campaign/project grouping evidence, not duplicate portfolios.
- Ambiguous matches remain staged for human review and must not auto-merge.

### Rollback plan

The pilot must run as a dry run first. Rollback before acceptance discards staged candidates and reports while preserving source files unchanged. Rollback after any future accepted ledger event must use compensating canonical events that mark candidates rejected, duplicate, superseded, or migration-aborted; source artifacts remain authoritative and are not rewritten by rollback.

## MIG-PTM-001B pilot migration execution package draft

A future executable package may execute only the accepted pilot slice from MIG-PTM-001A. It must be bounded to dry-run-first migration of the PTM work-package library metadata and may proceed to append-only ledger events only after Chief Architect review of the dry-run report.

### Future package objective

Execute the accepted PTM work-package-library pilot migration by producing deterministic file-import reports, governed intake candidates, duplicate decisions, dispatch evidence-chain links, validation evidence, and an acceptance/rollback report.

### Future package scope

Allowed:
- read the accepted pilot source paths;
- calculate source SHA-256 values;
- produce a dry-run file-import report;
- stage governed intake candidates for package, campaign, dependency, and evidence records;
- produce duplicate, validation, and dispatch-evidence-chain reports;
- prepare append-only event payload previews for review.

Not allowed:
- broad repository migration outside the accepted slice;
- source Markdown or manifest rewrites;
- production PTM code changes unless separately authorized;
- self-acceptance of migration output;
- a second dispatch queue, registry, scheduler, or governance authority.

### Future package validation gates

1. Dependency gate: confirm DISPATCH-PTM-001 and MIG-PTM-001A are accepted.
2. Source gate: all pilot source paths exist or are explicitly reported as missing.
3. Hash gate: every imported source has a SHA-256 mapping.
4. Dedupe gate: every proposed record has a duplicate decision.
5. Dispatch evidence gate: every migrated task candidate has either linked dispatch evidence or an explicit `not_dispatched` state.
6. Dry-run review gate: Chief Architect reviews the dry-run report before any persistent event emission.
7. Rollback gate: rollback actions are listed for every staged or emitted record.

## Gate D reconciliation notes

- Dispatch evidence links tasks to source-backed work packages, evidence, validation, and acceptance without becoming a second queue.
- The pilot migration slice is limited to PTM work-package-library metadata and evidence artifacts.
- Migration execution remains a future bounded package and must run dry-run-first.
- All source records remain authoritative in place and are referenced by path, SHA-256, and canonical event/report identifiers.
- No frozen upstream event, ID, projection, intake, route, schedule, dispatch, or validation contract is redefined.
