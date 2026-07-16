# Estate PTM Read-only Source Inventory and Adapter Contracts

Status: Draft implementation-preparation artifact for PTM-01 Gate A
Campaign: PTM-01 — Read-only source inventory
Packages: CORE-PTM-001A, CORE-PTM-001B, CORE-PTM-001C
Date: 2026-07-16

## Authority and boundaries

This artifact is source-backed planning evidence for the PTM read-only adapter layer. It follows the accepted PTM baseline and does not authorize production implementation, a second dispatch queue, a second registry, a second scheduler, or any new governance authority.

The inventory preserves the current authoritative domains: Parking Lot rows, work-package files, dispatch queue rows, runtime evidence, validation reports, and acceptance records stay authoritative in place and are referenced by future PTM projections rather than copied into a replacement execution system.

## CORE-PTM-001A inventory — collaboration and work-package sources

Repository scope reviewed: `collaboration/work_packages/**`, `collaboration/parking_lot/**`, and `collaboration/promotions/**`.

| Source family | Current path pattern | Observed inventory | Read-only adapter intent | Notes and risks |
| --- | --- | ---: | --- | --- |
| Work-package lifecycle files | `collaboration/work_packages/{pending,claimed,open,completed,completions}/**` | 776 files under `collaboration/work_packages` | Expose package ID, title, status bucket, owner/lane text where present, dependencies, validation requirements, acceptance criteria, and evidence links. | Status is mostly path-derived; individual files use heterogeneous Markdown/JSON formats. |
| PTM planning and campaign manifests | `collaboration/work_packages/planning/**`, `collaboration/work_packages/campaigns/**` | 33 planning files and 9 campaign files | Expose accepted package/campaign/dependency manifests, launch groups, branch controls, frozen contract gates, and package handoff paths. | Manifests are planning authority, not runtime registries. |
| Completion receipts | `collaboration/work_packages/completions/**` | 278 receipt files | Expose package ID, changed files, commands run, validation outcomes, limitations, and receipt timestamp if present. | Receipt schemas vary between Markdown and JSON. |
| Parking Lot items | `collaboration/parking_lot/**` | 5 files | Expose item ID, title, source file, triage/promotion state, and links to downstream package references when present. | Adapter must not mutate parking-lot rows or silently promote items. |
| Promotion records | `collaboration/promotions/**` | 4 files | Expose promotion request/approval/rejection state and source-to-package mapping evidence. | Promotion records remain governance evidence, not a new approval authority. |

### CORE-PTM-001A adapter fields

Minimum read model fields for this source slice:

- `source_path`
- `source_family`
- `source_status_bucket`
- `package_or_item_id`
- `title`
- `authority_refs`
- `dependency_refs`
- `validation_refs`
- `completion_receipt_refs`
- `promotion_refs`
- `parse_confidence`
- `adapter_warnings`

## CORE-PTM-001B inventory — dispatch, validation, resident, and operations sources

Repository scope reviewed: `collaboration/**` and `docs/architecture/**`, with targeted discovery for dispatch, validation, resident, Helen, Grace, Traffic Controller, and operations artifacts.

| Source family | Current path pattern or term match | Observed inventory | Read-only adapter intent | Notes and risks |
| --- | --- | ---: | --- | --- |
| Dispatch artifacts | `*dispatch*` under `collaboration/**` | 12 files | Expose dispatch package/evidence references and lifecycle closure records without creating a parallel dispatch queue. | Dispatch readiness and execution authority remain with existing governance paths. |
| Validation artifacts | `*validation*` under `collaboration/**` | 76 files | Expose validation recipes, reports, checklists, outcomes, and evidence paths. | Adapter must distinguish deterministic validation evidence from reviewer commentary. |
| Resident artifacts | `*resident*` under `collaboration/**`; resident references in architecture docs | 109 collaboration files and 1 architecture filename match | Expose resident-related package/evidence links and command-surface references. | Do not create or synchronize a second resident registry. |
| Helen artifacts | `*helen*` under `collaboration/**` | 19 files | Expose Helen-related staffing/HR/lock/evidence references. | Helen remains visible as an existing authority/persona boundary, not budget authority. |
| Grace artifacts | `*grace*` under `collaboration/**` | 11 files | Expose Grace-related operations/lock/evidence references. | Preserve Grace boundary and do not conflate with Traffic Controller. |
| Traffic Controller artifacts | `*traffic*` under `collaboration/**` | 3 files | Expose operational routing/control references and source evidence. | No new routing authority is introduced. |
| Operations artifacts | `*operation*` under `collaboration/**`; architecture operations docs | 78 collaboration files and 3 architecture filename matches | Expose operations packages, reports, panels, activity records, and governance references. | Operations records are source evidence for PTM projections, not a replacement operations center. |
| Architecture PTM baseline | `docs/architecture/estate_project_task_management_*.md`, PTM campaign plans | 24 architecture files | Expose source-backed constraints, domain boundaries, roadmap phases, data model fields, KPI definitions, and implementation gates. | Frozen upstream contracts must not be redefined by adapters. |

### CORE-PTM-001B adapter fields

Minimum read model fields for this source slice:

- `source_path`
- `source_family`
- `artifact_id`
- `title`
- `governance_actor_refs`
- `dispatch_refs`
- `validation_refs`
- `resident_refs`
- `operations_refs`
- `architecture_constraint_refs`
- `parse_confidence`
- `adapter_warnings`

### CORE-PTM-001B evidence notes

The inventory counts above were revalidated from the current branch on 2026-07-16 using bounded filename discovery within the authorized repository scope. The source families are intentionally path and term based because this package is a read-only inventory slice, not a schema freeze or production parser implementation. Future adapter implementation should preserve these source paths as provenance and emit low-confidence warnings for heterogeneous Markdown or JSON records rather than normalizing them into a new authoritative registry.

Evidence commands used for this slice:

```bash
find collaboration -type f -iname '*dispatch*' | wc -l
find collaboration -type f -iname '*validation*' | wc -l
find collaboration -type f -iname '*resident*' | wc -l
find collaboration -type f -iname '*helen*' | wc -l
find collaboration -type f -iname '*grace*' | wc -l
find collaboration -type f -iname '*traffic*' | wc -l
find collaboration -type f -iname '*operation*' | wc -l
find docs/architecture -type f -iname '*operation*' | wc -l
find docs/architecture -type f -iname 'estate_ptm*.md' -o -iname 'estate_project_task_management*.md' | wc -l
find docs/architecture -type f -iname '*resident*' | wc -l
```

## CORE-PTM-001C draft adapter contract

### Contract principles

1. Adapters are read-only and path-addressed.
2. Adapters emit normalized references and warnings; they do not mutate source files.
3. Adapters preserve source authority and expose provenance for every projected field.
4. Unknown, missing, or contradictory data is represented as uncertainty, not guessed.
5. Adapter output is not a second queue, registry, scheduler, validation authority, or governance authority.

### Draft adapter names

| Adapter name | Source coverage | Output responsibility |
| --- | --- | --- |
| `work_package_source_adapter` | `collaboration/work_packages/**` | Work-package lifecycle, package metadata, validation requirements, completion receipts, manifest links. |
| `parking_lot_source_adapter` | `collaboration/parking_lot/**` | Parking Lot item references and triage/promotion linkage. |
| `promotion_source_adapter` | `collaboration/promotions/**` | Promotion request/decision evidence and source-to-package linkage. |
| `dispatch_source_adapter` | Existing dispatch-named collaboration artifacts | Dispatch reference/evidence linkage only; no queue writes. |
| `validation_source_adapter` | Validation-named collaboration artifacts | Validation recipe/report/checklist/evidence summaries. |
| `resident_operations_source_adapter` | Resident, Helen, Grace, Traffic Controller, and operations artifacts | Governance actor references, operational evidence, and command-surface links. |
| `architecture_constraint_adapter` | `docs/architecture/**` PTM and operations architecture docs | Accepted boundaries, non-goals, gates, roadmap phases, data-model/KPI constraints. |

### Shared output envelope

All adapters should emit records with this envelope before downstream schema packages freeze canonical event/projection details:

```yaml
adapter_record:
  adapter_name: string
  adapter_version: "draft-ptm-01"
  source_path: string
  source_sha256: string
  source_family: string
  discovered_at: string
  extracted_id: string | null
  extracted_title: string | null
  extracted_status: string | null
  authority_refs: [string]
  dependency_refs: [string]
  evidence_refs: [string]
  related_source_paths: [string]
  parse_confidence: high | medium | low
  adapter_warnings: [string]
```

### Unresolved questions for downstream packages

- Which receipt JSON keys and Markdown headings should become canonical after the event and projection freeze?
- Should path-derived work-package status be authoritative when file body status disagrees with directory bucket?
- What minimum confidence threshold should block a source from appearing in resident-facing PTM views?
- Which dispatch evidence fields are safe to expose before DISPATCH-PTM-001 hardens runtime integration?
- How should archived, rejected, or superseded promotion records appear in portfolio rollups?

## Gate A evidence summary

- CORE-PTM-001A inventory completed as a bounded read-only source inventory.
- CORE-PTM-001B inventory completed as a bounded read-only source inventory.
- CORE-PTM-001C adapter contract draft completed from the two inventories.
- No production PTM code was added.
- No second dispatch queue, second registry, second scheduler, or new governance authority was introduced.

## CORE-PTM-001C implementation-ready adapter contract freeze draft

This section freezes the Gate A adapter contract names and minimum behavior for downstream PTM planning. It is a draft contract for future implementation packages only; it does not add executable adapters or change source authority.

### Contract status

- Contract version: `ptm-01-gate-a-draft`.
- Contract owner for review: Chief Architect.
- Source baseline: CORE-PTM-001A collaboration/work-package inventory and CORE-PTM-001B dispatch/validation/resident/operations inventory.
- Downstream use: CORE-PTM-002A and later packages may reference these adapter names and source categories, but must not treat this draft as production parser code.

### Adapter contract catalog

| Adapter name | Required source roots | Required discovery mode | Required minimum extracted fields | Required uncertainty behavior | Prohibited behavior |
| --- | --- | --- | --- | --- | --- |
| `work_package_source_adapter` | `collaboration/work_packages/**` | Enumerate lifecycle buckets, root work-package Markdown files, planning manifests, campaign instructions, queue files, claimed/open markers, completions, and completed receipts. | `source_path`, `source_family`, `source_status_bucket`, `package_or_item_id`, `title`, `authority_refs`, `dependency_refs`, `validation_refs`, `completion_receipt_refs`, `parse_confidence`, `adapter_warnings`. | Prefer explicit headings and manifest fields; when directory bucket and body status conflict, emit both via `extracted_status` plus warning. | Must not create, reorder, claim, close, or dispatch work packages. |
| `parking_lot_source_adapter` | `collaboration/parking_lot/**` | Enumerate Parking Lot Markdown candidates and preserve candidate path provenance. | `source_path`, `source_family`, `package_or_item_id`, `title`, `promotion_refs`, `authority_refs`, `parse_confidence`, `adapter_warnings`. | Treat parking-lot records as candidates until governed intake confirms promotion. | Must not silently promote, dedupe, reject, or prioritize parking-lot items. |
| `promotion_source_adapter` | `collaboration/promotions/**` | Enumerate promotion state directories and files, including empty `.gitkeep`-only state. | `source_path`, `source_family`, `source_status_bucket`, `package_or_item_id`, `promotion_refs`, `related_source_paths`, `parse_confidence`, `adapter_warnings`. | Emit low-confidence records for structural placeholders with no substantive promotion payload. | Must not approve, reject, or replace any promotion authority. |
| `dispatch_source_adapter` | Dispatch-named artifacts under `collaboration/**` | Enumerate dispatch packages, evidence files, reports, and closure records by path/name evidence. | `source_path`, `source_family`, `artifact_id`, `title`, `dispatch_refs`, `evidence_refs`, `authority_refs`, `parse_confidence`, `adapter_warnings`. | Warn when dispatch evidence is documentary rather than runtime-confirmed. | Must not create a second dispatch queue or mutate dispatch readiness. |
| `validation_source_adapter` | Validation-named artifacts under `collaboration/**` | Enumerate validation recipes, checklists, reports, package receipts, and evidence links by path/name evidence. | `source_path`, `source_family`, `artifact_id`, `title`, `validation_refs`, `evidence_refs`, `parse_confidence`, `adapter_warnings`. | Distinguish commands run, expected validation, reviewer notes, skipped checks, and environment limitations where detectable. | Must not mark packages accepted or override reviewer validation. |
| `resident_operations_source_adapter` | Resident, Helen, Grace, Traffic Controller, and operations artifacts under `collaboration/**` plus named architecture references. | Enumerate source files with resident, Helen, Grace, Traffic Controller, and operations evidence. | `source_path`, `source_family`, `artifact_id`, `title`, `governance_actor_refs`, `resident_refs`, `operations_refs`, `authority_refs`, `parse_confidence`, `adapter_warnings`. | Preserve actor names as references, not authority grants; warn when files mention multiple governance actors with unclear role boundaries. | Must not create a resident registry, staffing ledger, budget authority, or routing authority. |
| `architecture_constraint_adapter` | `docs/architecture/**` PTM and operations architecture documents | Enumerate accepted PTM baseline, campaign plan, dependency plan, data-model, KPI, roadmap, financial, scheduling, utilization, and operations constraint documents. | `source_path`, `source_family`, `artifact_id`, `title`, `architecture_constraint_refs`, `authority_refs`, `dependency_refs`, `parse_confidence`, `adapter_warnings`. | Emit constraints as source-backed references; when a downstream package proposes a conflicting contract, stop for replan rather than resolving locally. | Must not redefine frozen upstream contracts or create new governance boundaries. |

### Normalization and provenance requirements

Every adapter record must preserve enough provenance to re-open the original source and verify the projection. The shared envelope remains intentionally pre-canonical until CORE-PTM-002A, CORE-PTM-002B, CORE-PTM-003A, and CORE-PTM-003B freeze event and projection contracts.

Required envelope fields:

- `adapter_name`: one of the seven names in the adapter contract catalog.
- `adapter_version`: `ptm-01-gate-a-draft` until a later accepted package changes it.
- `source_path`: repository-relative path to the original source file or structural directory marker.
- `source_sha256`: hash of the source file content where a file exists; `null` only for directory-only structural observations.
- `source_family`: stable family label from the adapter catalog.
- `discovered_at`: ISO-8601 timestamp for the inventory run that produced the record.
- `extracted_id`: package, parking-lot, artifact, or architecture identifier when detectable.
- `extracted_title`: title or heading when detectable.
- `extracted_status`: explicit status or path-derived bucket when detectable.
- `authority_refs`: source-backed authority, owner, reviewer, or governance references.
- `dependency_refs`: source-backed package, campaign, or readiness dependencies.
- `evidence_refs`: source-backed validation, receipt, report, or completion evidence references.
- `related_source_paths`: additional paths directly referenced by the source record.
- `parse_confidence`: `high`, `medium`, or `low`.
- `adapter_warnings`: non-fatal uncertainty, contradiction, missing-field, placeholder, or boundary warnings.

### Parse-confidence guidance

| Confidence | Required evidence | Example use |
| --- | --- | --- |
| `high` | Explicit ID/status/title fields or manifest keys with consistent path evidence. | Pending PTM package with clear package ID, status, dependencies, scope, and validation headings. |
| `medium` | Clear path/name evidence plus partial body evidence, or heterogeneous records with enough headings to classify safely. | Markdown completion receipt with commands and deliverables but no machine-readable status key. |
| `low` | Placeholder, structural-only, contradictory, or filename-only evidence. | `.gitkeep` promotion state marker or artifact with actor term match but unclear PTM relevance. |

### Downstream freeze handoff

- CORE-PTM-002A may reference `adapter_name`, `adapter_version`, `source_path`, `source_sha256`, and evidence/reference arrays when drafting append-only event semantics.
- CORE-PTM-002B may reference `extracted_id`, command envelope provenance, and source hash fields when drafting ID and command contract behavior.
- CORE-PTM-003A and CORE-PTM-003B may reference extracted status, dependency, validation, schedule, financial, KPI, and actor-reference fields for projection planning.
- Any downstream package that needs to rename an adapter, add a required field, or change a prohibited behavior must stop and open a replan note because Gate A adapter names are shared fan-out assumptions.

### CORE-PTM-001C unresolved-question log

| Question | Affected future package(s) | Current Gate A disposition |
| --- | --- | --- |
| Which Markdown headings and JSON keys become canonical receipt fields? | CORE-PTM-002A, CORE-PTM-003A, TEST-PTM-001A | Defer to event/projection freeze; adapters expose raw evidence and warnings now. |
| Should path-derived lifecycle status override body status when they conflict? | CORE-PTM-002A, CORE-PTM-003A, UI-PTM-001A | Do not override at adapter layer; emit both with a warning until canonical projections decide precedence. |
| What confidence threshold is safe for resident-facing views? | UI-PTM-001A, UI-PTM-001B, CONV-PTM-001, TEST-PTM-001A | Defer to UI/conversation validation; adapters emit confidence only. |
| Which dispatch evidence fields are safe before runtime dispatch integration hardens? | DISPATCH-PTM-001, MIG-PTM-001A, TEST-PTM-001B | Treat dispatch artifacts as references only; no readiness mutation or queue write. |
| How should archived, rejected, superseded, or placeholder promotion records appear in portfolio rollups? | INTAKE-PTM-001A, INTAKE-PTM-001B, KPI-PTM-001 | Preserve promotion state and low-confidence placeholder warnings; defer rollup semantics. |
| Should source hashes be recalculated on every projection read or captured only at import time? | CORE-PTM-002B, MIG-PTM-001A, TEST-PTM-001B | Require hash presence in adapter records; timing and storage semantics defer to event/ID contract packages. |
