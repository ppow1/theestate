# Estate Project and Task Management Implementation Roadmap

## Phase 0: specification acceptance

Accept architecture, protocol, data model, UX, catalog, roadmap, and backlog. Gate: Chief Architect review confirms no second execution system.

## Phase 1: read-only discovery and projection pilot

Build read-only adapters over Parking Lot, work packages, dispatch queue, validation, acceptance, Helen, Grace, Traffic Controller, and activity artifacts. Gate: no mutation; source paths and uncertainty reported.

## Phase 2: core event ledger

Implement append-only event store, ID minting, projections, hash chain, migration dry runs, and audit timeline. Gate: projections rebuild deterministically.

## Phase 3: governed intake

Implement Parking Lot promotion, manual entry, resident/conference commands, and file import with dedupe and source mappings. Gate: duplicate imports are safe and auditable.

## Phase 4: workspace MVP

Implement Portfolio, Projects, Task Ledger, Task detail, Intake, Audit Timeline, Archive/Trash, and Office compact card. Gate: Office stays compact.

## Phase 5: scheduling and capacity

Add schedule fields, dependency/critical path, reservations, calendars, blocked intervals, provider quotas, and compute conflicts. Gate: dispatch readiness checks enforce gates.

## Phase 6: financials and utilization

Add budget references, estimates, actual costs, allocation methods, local/external comparison, utilization telemetry ingestion, and reconciliation. Gate: no Helen/Grace budget authority.

## Phase 7: KPI catalog

Publish KPI registry, observations, data-quality controls, baselines, targets, and workspace dashboards. Gate: missing data remains explicit.

## Phase 8: dispatch and runtime integration hardening

Link task/work-package/dispatch/evidence/validation/acceptance chain end-to-end through existing queues and bridges. Gate: no parallel dispatch queue.

## Phase 9: rollout and migration

Migrate selected current work, pilot with one portfolio, train residents, validate operational reports, then expand. Gate: audit and acceptance records reconcile.

## Risks

Scope creep into implementation, accidental second execution path, KPI false precision, graph unreadability, private evidence exposure, stale projections, budget-boundary confusion, and migration duplicates.

## Recommended pilot

One portfolio, five Parking Lot items, two existing work packages, one dispatch evidence chain, one validation result, one acceptance decision, compact Office card, and three KPIs: cycle time, audit completeness, and blocked duration.

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
