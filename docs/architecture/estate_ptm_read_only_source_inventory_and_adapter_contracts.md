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
