# SERIES TASK WP-0029 — Artifact Provenance Model

## Codex Command
Read `collaboration/work_packages/pending/WP-0029_SERIES_artifact_provenance_model.md` and do exactly what it says.

## Mode
SERIES. Depends on WP-0026 Generated Artifact Policy and WP-0028 Document Registry.

## Mission
Implement a lightweight Artifact Provenance Model so Estate artifacts can record whether they are proposed, authored, generated, reviewed, validated, superseded, or institutional evidence.

## Why This Is Next
The Estate now has authored documents, generated reports, work packages, completion records, review records, registries, dashboards, and institutional memory. Workers need a consistent way to identify where an artifact came from, who or what created it, and how much trust should be placed in it.

## Scope
Create a bounded provenance schema/document and helper support.

Possible outputs:

- `docs/operations/Artifact_Provenance_Model_v1.md`
- `data/registry/artifact_provenance_schema.json`
- optional helper module such as `src/estate/core/artifact_provenance.py`

## Provenance Fields
Define fields such as:

- artifact_id
- path
- artifact_type
- provenance_state
- created_by
- generated_by
- source_inputs
- reviewed_by
- validation_status
- supersedes
- superseded_by
- notes

## Required States
Support at least:

- proposed
- authored
- generated
- reviewed
- validated
- institutional_evidence
- superseded
- unresolved

## Expected Outputs
- Provenance model documentation.
- Machine-readable schema if straightforward.
- Optional CLI/helper to emit provenance records for known artifact paths.
- Tests if code is added.

## Constraints
Do not migrate every existing artifact. Do not redesign document registry. Do not make generated artifacts authoritative. Do not create new governance authority. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Validation
If code is added, run relevant tests. If documentation/schema only, validate JSON schema parses and referenced paths exist where appropriate.

## Completion Signal
Before finishing, create `collaboration/work_packages/completions/WP-0029_codex_done.json` with work_package_id, codex_status=done, completed_at, branch, pull_request_url, summary, files_changed, tests_run, known_limitations, ready_for_ca_review=true, merge_authority=ca_verified_auto_merge_allowed.

## Merge Class
Class A — bounded provenance model. Escalate to Class B only if implementation changes source-of-truth authority or governance.
