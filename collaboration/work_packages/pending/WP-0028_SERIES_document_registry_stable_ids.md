# SERIES TASK WP-0028 — Document Registry and Stable Document IDs

## Codex Command
Read `collaboration/work_packages/pending/WP-0028_SERIES_document_registry_stable_ids.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0026 Generated Artifact Policy and benefits from WP-0027 Institutional Search.

## Mission
Create the first stable Document Registry so important Estate documents can be referenced by durable IDs instead of fragile paths or memory.

## Why This Is Next
Onboarding exposed path drift. Workers need stable references to constitutional, governance, collaboration, operations, onboarding, visual, and institutional memory documents. Paths may change, but document identity should remain stable.

## Scope
Add a machine-readable registry such as:

- `data/registry/documents.json`

and a human-readable view such as:

- `docs/operations/Document_Registry_v1.md`

## Registry Requirements
Each document entry should include:

- stable document ID
- display title
- current repository-relative path
- category
- required/optional status where relevant
- audience
- source-of-truth classification
- notes
- superseded paths if known

## Initial Registry Coverage
Include, where present:

- `AI_HINTS.md`
- `AI_START_HERE.md`
- `constitution/constitution.md`
- onboarding manifests
- visual manifest
- Estate Orientation Handbook
- Estate Manual
- collaboration layer docs
- branch management standard
- worker launch docs
- operations board docs
- capability lifecycle docs
- operational validation docs
- Chief Architect memoranda
- Generated Artifact Policy

## Expected Outputs
- Document registry JSON.
- Human-readable registry document.
- Optional CLI/helper if consistent with existing patterns, for example:

```bash
PYTHONPATH=src python -m estate.cli.main document-registry --json
```

## Constraints
Do not move files. Do not rename files. Do not invent missing documents. Unresolved documents must be marked unresolved. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Add tests for:

- registry file exists
- required paths exist or are explicitly unresolved
- stale Constitution path is not used as current path
- stable IDs are unique
- JSON schema basics

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0028_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded registry/documentation implementation after CA verification. Escalate to Class B only if implementation changes governance authority or moves canonical files.
