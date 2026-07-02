# Artifact Provenance Model v1

Status: Active Model
Owner: Chief Architect / Alfred Operations
Classification: Estate Internal
Introduced By: WP-0029
Date: 2026-07-02

## Purpose

The Artifact Provenance Model gives Estate workers a lightweight way to describe where an artifact came from, who or what created it, what review or validation evidence exists, and whether the artifact has been superseded.

This model is descriptive. It does not create new governance authority, does not make generated artifacts authoritative, and does not replace the Document Registry or Generated Artifact Policy.

## Relationship to Existing Estate Records

Use this model alongside, not instead of, existing Estate records:

- The Document Registry identifies durable Estate documents and their current paths.
- The Generated Artifact Policy explains how authored source artifacts, generated projections, runtime artifacts, committed summaries, and institutional evidence should be treated.
- Work package completions, reviews, validation records, and promotion records remain evidence records in their existing locations.

A provenance record may point to those records, but it does not promote, approve, validate, or supersede an artifact by itself.

## Provenance Record Shape

A provenance record is a JSON object matching `data/registry/artifact_provenance_schema.json` when machine validation is needed.

| Field | Required | Type | Description |
|---|---:|---|---|
| `artifact_id` | yes | string | Stable local identifier for the artifact or provenance record. Prefer an existing document/work-package/record ID when available. |
| `path` | yes | string | Repository-relative path to the artifact being described. |
| `artifact_type` | yes | string | Human-readable type, such as `document`, `registry`, `work_package`, `completion_record`, `review_record`, `generated_projection`, `runtime_projection`, `asset`, or `other`. |
| `provenance_state` | yes | string | Current provenance state from the required state vocabulary. |
| `created_by` | no | string or null | Human, worker, role, or institution that authored or initiated the artifact. |
| `generated_by` | no | string or null | Tool, command, worker, or automation that generated the artifact. Use only when applicable. |
| `source_inputs` | no | array | Repository-relative paths, IDs, or short descriptors for inputs used to create or generate the artifact. |
| `reviewed_by` | no | array | People, roles, workers, or review record IDs that reviewed the artifact. |
| `validation_status` | no | string | Validation posture, such as `not_checked`, `pending`, `passed`, `failed`, `warning`, or `not_applicable`. |
| `supersedes` | no | array | Artifact IDs or paths this artifact replaces. |
| `superseded_by` | no | array | Artifact IDs or paths that replace this artifact. |
| `notes` | no | string | Short explanatory note, limitation, or reviewer guidance. |

## Required Provenance States

| State | Meaning | Authority Guidance |
|---|---|---|
| `proposed` | Artifact is drafted, requested, or queued but not accepted as active Estate guidance or evidence. | Use for work packages, proposals, and draft records. |
| `authored` | Artifact was intentionally written or maintained by a human, worker, or authorized Estate role. | May be authoritative only if an existing policy, registry, or governance record already makes it so. |
| `generated` | Artifact was produced by tooling, automation, summarization, or a worker-generated process. | Derived view only; generated status never makes it source of truth. |
| `reviewed` | Artifact has been reviewed and has review evidence. | Review evidence should be cited in `reviewed_by` or `source_inputs`; review alone does not imply validation. |
| `validated` | Artifact or its generation process passed a defined validation check. | Validation evidence should be traceable; validation does not override higher-authority source records. |
| `institutional_evidence` | Artifact records that work occurred, was reviewed, was completed, or was accepted as evidence. | Evidence of process or completion, not automatic proof that all underlying content is correct. |
| `superseded` | Artifact has been replaced by another artifact. | Prefer the artifact listed in `superseded_by` and retain this record for traceability. |
| `unresolved` | Provenance cannot yet be determined. | Treat conservatively and avoid authority-sensitive reliance until reviewed. |

## Validation Status Values

Recommended values are:

- `not_checked` — no validation has been performed or recorded.
- `pending` — validation is expected but incomplete.
- `passed` — relevant validation completed successfully.
- `failed` — validation found a blocking issue.
- `warning` — validation completed with non-blocking concerns or environmental limitations.
- `not_applicable` — validation is not meaningful for this artifact.

## Minimal Examples

### Authored Document

```json
{
  "artifact_id": "DOC-GENERATED-ARTIFACT-POLICY",
  "path": "docs/operations/Generated_Artifact_Policy_v1.md",
  "artifact_type": "document",
  "provenance_state": "authored",
  "created_by": "Chief Architect / Alfred Operations",
  "generated_by": null,
  "source_inputs": [],
  "reviewed_by": [],
  "validation_status": "not_applicable",
  "supersedes": [],
  "superseded_by": [],
  "notes": "Authored policy document; authority comes from existing governance context, not from this provenance record."
}
```

### Generated Projection

```json
{
  "artifact_id": "PROJ-WORKER-INBOX-SUMMARY",
  "path": "collaboration/status/worker_inbox_summary.json",
  "artifact_type": "generated_projection",
  "provenance_state": "generated",
  "created_by": null,
  "generated_by": "collaboration status tooling",
  "source_inputs": [
    "collaboration/messages/*.json",
    "data/registry/personnel.json"
  ],
  "reviewed_by": [],
  "validation_status": "not_checked",
  "supersedes": [],
  "superseded_by": [],
  "notes": "Operational projection only; inspect source messages for authority-sensitive decisions."
}
```

### Completion Evidence

```json
{
  "artifact_id": "WP-0029-CODEX-DONE",
  "path": "collaboration/work_packages/completions/WP-0029_codex_done.json",
  "artifact_type": "completion_record",
  "provenance_state": "institutional_evidence",
  "created_by": "Codex",
  "generated_by": null,
  "source_inputs": [
    "collaboration/work_packages/pending/WP-0029_SERIES_artifact_provenance_model.md"
  ],
  "reviewed_by": [],
  "validation_status": "pending",
  "supersedes": [],
  "superseded_by": [],
  "notes": "Completion signal for CA review; not proof that review has accepted the work."
}
```

## Worker Expectations

1. Prefer existing authoritative records for decisions; use provenance records for traceability.
2. Use `generated` for derived outputs even when they are committed to the repository.
3. Use `institutional_evidence` for completion, review, promotion, and history records that document process.
4. Use `unresolved` when provenance is uncertain instead of guessing authority.
5. Record supersession in both directions when practical: the old record should name `superseded_by`, and the new record should name `supersedes`.
6. Keep notes concise and avoid copying private Local Only runtime details into committed provenance records.

## Non-Goals

This model does not:

- migrate every existing artifact into provenance records;
- redesign the Document Registry;
- change the Generated Artifact Policy;
- make generated projections authoritative;
- create new promotion, approval, review, or governance authority.
