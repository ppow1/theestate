# Estate Project and Task Management Protocol

## Canonical objects

Objects: Portfolio, Project, Task, TaskBranch, TaskRelationship, WorkPackageSpec, DispatchAttempt, ExecutionResult, ValidationResult, AcceptanceDecision, ProjectTaskEvent, IntakeItem, ScheduleReservation, CapacityReservation, UtilizationObservation, CostEstimate, BudgetRequestApprovalReference, ActualCostRecord, KPIDefinition, KPIObservation, AuditProvenanceRecord.

## Lifecycle state machines

- Project: `proposed -> planned -> active -> blocked -> completing -> completed -> archived`; alternate terminal states are `cancelled` and `abandoned`.
- Task: `captured -> triaged -> planned -> ready_for_staffing -> staffing_ready -> ready_for_operations -> ready_for_dispatch -> dispatched -> executed -> validating -> awaiting_acceptance -> accepted -> closed`; reversible states include `blocked`, `deferred`, `reopened`, `trashed`, and `archived`.
- Branch: `proposed -> exploring -> selected | superseded | abandoned | merged`.

## Safe operations

Create, edit, reprioritize, schedule, assign, defer, disable, cancel, archive, trash, restore, reopen, add/remove from project, move between projects, split, merge duplicates, create alternatives, select winning branch, abandon/supersede branches, add/remove dependencies, preserve failed experiments, promote to current production, and return to planning/backlog all emit events with reason and actor. Identity is preserved; structure changes are relationship events.

Relationship fields: `parent`, `child`, `depends_on`, `blocks`, `supersedes`, `superseded_by`, `alternative_to`, `derived_from`, `split_from`, `merged_into`.

## Event protocol

Events are append-only and include event ID, schema version, object type, object ID, actor, actor type, source surface/system, timestamp, prior and resulting state, reason, evidence/artifact references, conversation/room/file-import/work-package/dispatch/validation references, correlation ID, causation ID, integrity hash, classification, and visibility.

## Intake protocol

Supported paths: Parking Lot promotion; conference-room/resident commands; manual workspace entry; file intake from ChatGPT, Codex, or approved sources. File intake preserves source filename, system, SHA-256, import timestamp, importer, accepted/rejected items, duplicates, warnings, and mappings.

Command examples require confirmation for material change: `create a task from this discussion`, `add this to PROJ-0001`, `change priority`, `move into current production`, `Helen assess staffing for TASK-0001`, `Grace take TASK-0001 after staffing readiness`, `show the full history of TASK-0001`.

## Scheduling protocol

Fields include planned/earliest/latest/actual start and finish, duration estimates, confidence range, dependencies, critical-path marker, milestones, recurring rule, calendars, compute/model conflicts, validation and acceptance windows, maintenance, blocked intervals, priority insertions, forecasts, capacity reservations, provider quotas, and budget gates.

## Utilization protocol

Mandatory: worker/provider availability state, committed capacity, active/blocked/idle markers, assignment queue age, validation/rework time, provider quotas where applicable. Optional or telemetry-derived: GPU active/reserved time, VRAM allocation/peak, CPU, RAM, storage, model cache, power, thermal, model load/unload time. Estimates must be marked.

## Financial protocol

Track estimated cost, budget requested, budget approved, spend authorized, committed cost, incurred cost, accepted cost, forecast at completion, variance, remaining budget, contingency, provider charges, API/subscription allocation, electricity, local compute, storage, licensing, hardware depreciation, oversight time, rework, failed-branch cost, materials, cost center, currency, allocation method, cost of delay, and opportunity cost. Helen and Grace do not approve budgets.

## KPI protocol

KPI definitions declare formula, source events, data quality, period, baseline, target, thresholds, owner, and missing-data behavior. Observations are derived and attributable.

## Soft-delete protocol

Archive removes from default active views; trash marks reversible deletion; restore emits a restoring event; purge is prohibited while retention, legal hold, audit hold, or referenced evidence exists.

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
