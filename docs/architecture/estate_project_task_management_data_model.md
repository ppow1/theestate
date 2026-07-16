# Estate Project and Task Management Data Model

## ID namespaces

`PORT-0001`, `PROJ-0001`, `TASK-0001`, `BRANCH-0001`, `REL-0001`, `INTAKE-0001`, `SCHED-0001`, `CAP-0001`, `UTIL-0001`, `COST-0001`, `BUD-0001`, `KPI-0001`, `KPIOBS-0001`, `AUD-0001`. Imported source IDs are stored separately and mapped.

## Schema skeletons

```yaml
project:
  id: PROJ-NNNN
  portfolio_id: PORT-NNNN
  title: string
  status: proposed|planned|active|blocked|completed|cancelled|archived|trashed
  priority: critical|high|normal|low
  owner_ref: actor-id
  budget_ref: optional BUD-NNNN
  classification: string
  created_event_id: EVT-NNNN
  current_version: integer

task:
  id: TASK-NNNN
  project_ids: [PROJ-NNNN]
  title: string
  status: captured|triaged|planned|staffing_ready|ready_for_dispatch|dispatched|executed|validating|awaiting_acceptance|accepted|closed|blocked|deferred|reopened|archived|trashed
  branch_ids: [BRANCH-NNNN]
  relationship_ids: [REL-NNNN]
  work_package_refs: [path-or-WP-id]
  dispatch_attempt_ids: [DISP-NNNN]
  validation_refs: [artifact-ref]
  acceptance_refs: [artifact-ref]
  schedule_ref: SCHED-NNNN
  capacity_refs: [CAP-NNNN]
  cost_refs: [COST-NNNN]
  classification: string

event:
  event_id: EVT-NNNN
  schema_version: 1
  object_type: task|project|branch|relationship|intake|schedule|capacity|cost|kpi
  object_id: string
  event_type: string
  actor: string
  actor_type: resident|office|worker|system|steward|chief_architect
  source_surface: string
  timestamp: ISO-8601
  prior_state: object|null
  resulting_state: object|null
  reason: string
  evidence_refs: [uri]
  correlation_id: string
  causation_id: string|null
  previous_hash: string|null
  event_hash: string
  classification: string
  visibility: public|estate_internal|restricted|steward_only|local_only
```

## Projections

Projection tables include `project_current`, `task_current`, `task_relationship_index`, `branch_graph`, `schedule_projection`, `capacity_projection`, `financial_projection`, `kpi_observation_projection`, `audit_timeline`, and `office_summary_projection`. They are rebuildable and never canonical.

## Provenance and integrity

Every event stores previous hash and event hash over canonical JSON. Evidence references store path/URI, source system, content hash when available, classifier, and visibility. Migration uses batch IDs and source-to-created-object mappings.

## Versioning and migration

Schemas are versioned. Breaking changes require migration events, reversible mapping files, dry-run reports, and projection rebuild validation. IDs remain stable across split, merge, branch, import, and migration.

## Required analysis answers

- **Canonical source of truth:** the append-only Project Task Management event log plus immutable referenced evidence. Current tables, cards, and workspace views are projections.
- **Projection rebuild:** projections are deleted and replayed from ordered events, validating schema version, hash chain, and causation references.
- **ID preservation:** IDs are minted once by namespace (`PORT-`, `PROJ-`, `TASK-`, `BRANCH-`, `WP-`, `DISP-`, `INTAKE-`, `KPI-`, `COST-`) and never reused; import mappings, split/merge/branch events preserve source and descendant IDs.
- **References vs canonical objects:** Parking Lot rows, work-package files, dispatch queue rows, runtime evidence, validation reports, and acceptance records remain authoritative in their domains and are referenced by canonical project/task objects rather than copied into a second execution system.
- **Duplicates:** duplicate detection uses normalized title, source hash, source object ID, semantic hints, and human confirmation; duplicates create `duplicate_detected` and optional `merged_into` events, never silent overwrites.
- **Retention:** archive hides from default planning; trash marks reversible removal; restore reverses trash/archive; legal/audit hold prevents purge; immutable events and evidence references remain retained.
- **Helen and Grace visibility:** task detail summarizes staffing readiness and operational supervision with links to evidence, hiding raw implementation noise by default.
- **Provider recommendations:** recommendations are advisory evidence; Traffic Controller/Operations decisions and budget gates authorize provider selection.
- **Dispatch readiness gates:** scheduling, capacity, budget, privacy/classification, validation-plan, read/write-boundary, and acceptance-owner checks must pass before Dispatch becomes Ready.
- **Cost reconciliation:** local and external estimates are evented, actuals are imported or telemetry-derived, and variances reconcile against accepted cost records.
- **KPI protection:** formulas declare required events, freshness, confidence, exclusions, owner, and manipulation controls; unknown values remain unknown.
- **Scale:** workspace relies on indexed projections, virtualized lists, progressive detail disclosure, saved filters, and graph condensation.
- **Branches:** branches are graph overlays on tasks, not deeply nested folders; winning, abandoned, superseded, and merged paths remain visible in a branch graph.
- **Smallest safe pilot:** ingest selected Parking Lot items into a read-only project/task ledger, link one existing work package and dispatch evidence, compute basic cycle-time and audit completeness KPIs, and expose a compact Office card without execution changes.
