# WP-0658 — Estate Project and Task Management Specification and Implementation Roadmap

Status: Pending
Owner: Chief Architect
Execution lane: Codex
Change class: Specification and architecture only

## Objective

Produce the canonical skeleton, specification, protocol, operating model, and implementation roadmap for an Estate-wide project and task management capability before implementation begins.

This package is a design and decomposition assignment. Do not build the production system in this work package.

## Context

The Estate now has working resident conversations, Helen workforce records, Grace operational actions, Traffic Controller decisions, Dispatch Queue items, an external Engineering Worker Runtime, validation evidence, and Chief Architect/Steward acceptance records. These artifacts are not yet unified into a single project-management backbone that supports planning, branching, scheduling, utilization, financials, KPIs, auditability, resident interaction, file intake, and a dedicated management workspace.

The Office of the Steward is already too crowded to host the full system. It should expose only a compact project/portfolio summary and links into a separate Project Management workspace.

## Mandatory design principles

1. Reuse existing Estate authorities, records, queues, and runtimes. Do not create a second execution system, second Dispatch Queue, or competing governance layer.
2. Preserve settled authority boundaries:
   - Helen owns personnel, capability assessment, qualifications, staffing readiness, and workforce development.
   - Grace owns operational supervision after staffing, including sequencing, scheduling, dispatch, monitoring, blockers, retries, escalation, and delivery.
   - Traffic Controller and Dispatch preserve routing, movement, provider, and execution boundaries.
   - Chief Architect and Steward retain institutional acceptance.
3. Every material state change must be auditable and attributable.
4. Operational values such as cycle time, cost, utilization, and KPI results must be derived from events and evidence whenever practical, not manually overwritten summary fields.
5. Deletion must be soft and reversible by default. History, provenance, and prior execution evidence must remain available.
6. The system must support both graphical Office workflows and governed conversational access by relevant residents.
7. This work package must produce specification artifacts and a sequenced implementation backlog, not a monolithic implementation.

## Required conceptual model

Define clear contracts and relationships for at least the following objects:

- Portfolio
- Project
- Task
- Task branch or alternative approach
- Task relationship
- Work package or bounded execution specification
- Dispatch attempt
- Execution result
- Validation result
- Acceptance decision
- Project/task event
- Intake item
- Schedule reservation
- Capacity reservation
- Utilization observation
- Cost estimate
- Budget request and approval reference
- Actual cost record
- KPI definition and KPI observation
- Audit/provenance record

Clearly distinguish:

Project -> Task -> Work Package or bounded execution specification -> Dispatch Attempt -> Execution Evidence -> Validation -> Acceptance

A task may exist before a work package. A task may have multiple dispatch attempts. A task or project may branch, split, merge, supersede, reopen, or abandon an approach without losing history.

## Required task and project flexibility

Specify safe operations for:

- create, edit, reprioritize, schedule, assign, defer, disable, cancel, archive, trash, restore, and reopen;
- add and remove tasks from projects;
- move tasks between projects;
- split one task into child tasks;
- merge duplicate tasks;
- create alternative branches;
- select a winning branch;
- abandon or supersede failed branches;
- add and remove dependencies;
- preserve failed experiments as institutional evidence;
- promote work into current production;
- return work to planning or backlog;
- preserve project and task identity across changes.

Define relationship fields such as parent, child, depends_on, blocks, supersedes, superseded_by, alternative_to, derived_from, split_from, and merged_into.

## Intake paths

Specify a single governed intake protocol supporting:

1. Parking Lot promotion into a project, standalone task, task under an existing project, or planning/research item.
2. Conference-room and resident conversation commands such as:
   - create a task from this discussion;
   - add this to an existing project;
   - change priority;
   - move into current production;
   - Helen assess staffing for TASK-NNNN;
   - Grace take TASK-NNNN after staffing readiness;
   - show the full history of TASK-NNNN.
3. Manual entry from the Project Management workspace.
4. File intake from ChatGPT, Codex, or other approved sources containing project plans, task lists, dependency maps, provider recommendations, work-package batches, or acceptance criteria.

The file-ingestion protocol must preserve source filename, source system, SHA-256, import timestamp, importer, accepted items, rejected items, duplicates, warnings, and source-to-created-object mappings.

## Scheduling requirements

Treat scheduling as a first-class subsystem. Specify fields, events, calculations, and views for:

- planned, earliest, latest, and actual start/finish;
- durations and confidence ranges;
- dependencies and critical path;
- milestones and deadlines;
- recurring work;
- worker/provider calendars and availability;
- local compute and model-loading conflicts;
- validation and acceptance windows;
- maintenance windows;
- blocked intervals and recovery;
- priority changes and emergency insertions;
- scenario planning and forecast changes;
- capacity reservations;
- external-provider quotas or turnaround constraints;
- budget approval gates before paid execution.

Include schedule events and KPIs such as on-time rate, schedule variance, milestone reliability, queue wait, blocker impact, forecast accuracy, capacity delay, priority-change disruption, and critical-path slippage.

## Capacity and utilization requirements

Specify worker, provider, project, and local-compute utilization models covering:

- available capacity;
- committed capacity;
- active productive capacity;
- blocked capacity;
- idle capacity;
- overcommitment;
- concurrent-work limits;
- queued assignments;
- validation and rework time;
- maintenance or unavailable periods;
- utilization by project and task type;
- GPU active and reserved time;
- VRAM allocation and peak VRAM;
- CPU, RAM, storage, model-cache, power, and thermal observations where available;
- model load/unload time;
- provider share, quotas, rate limits, and availability;
- local-versus-external routing mix.

Explain which utilization data is mandatory, optional, estimated, or telemetry-derived.

## Financial requirements

Specify support for:

- original and approved budget;
- budget requests and approvals;
- committed cost;
- actual cost;
- forecast at completion;
- variance;
- remaining budget;
- contingency;
- external provider charges;
- API/subscription allocation;
- electricity;
- local compute allocation;
- storage;
- licensing;
- hardware depreciation;
- operator oversight time;
- rework cost;
- failed-branch cost;
- materials and miscellaneous direct cost;
- cost centers and project references;
- currency and allocation method;
- estimated versus actual cost;
- local-versus-external routing comparisons;
- cost of delay and opportunity cost.

Preserve the distinction between estimated cost, budget requested, budget approved, spend authorized, cost incurred, and cost accepted. Do not grant budget authority to Helen or Grace.

## KPI requirements

Define a KPI registry with formulas, source events, data-quality rules, reporting periods, baselines, targets, trends, status thresholds, and owners.

Cover at least:

### Project KPIs
- completion rate;
- blocked percentage;
- overdue work;
- schedule variance;
- reopenings;
- failed and abandoned branches;
- validation pass rate;
- acceptance pass rate;
- forecast accuracy;
- estimated versus actual effort;
- velocity and throughput.

### Task KPIs
- creation-to-triage;
- triage-to-ready;
- ready-to-start;
- execution duration;
- validation duration;
- acceptance delay;
- total cycle time;
- retries;
- dispatch attempts;
- reopenings;
- blocker duration;
- branch changes;
- final outcome.

### Worker and provider KPIs
- completion rate;
- first-pass validation rate;
- failure and retry rate;
- median execution time;
- evidence completeness;
- scope violations;
- rework rate;
- blocker time;
- task-type suitability;
- utilization;
- cost and accepted work per dollar.

### Operational KPIs
- work in progress;
- throughput;
- queue age;
- dispatch backlog;
- validation backlog;
- acceptance backlog;
- on-time completion;
- escalation frequency;
- utilization and overcommitment;
- productive versus blocked utilization.

### Governance and quality KPIs
- provenance completeness;
- staffing evidence completeness;
- authorization-reference completeness;
- read/write-boundary completeness;
- validation coverage;
- failed-closed events;
- unauthorized execution attempts;
- acceptance without required evidence;
- audit-chain integrity;
- stale or missing ownership.

### Financial and efficiency KPIs
- budget variance;
- forecast variance;
- cost per completed and accepted task;
- rework cost rate;
- failed-branch cost;
- local versus external cost;
- spend by project and provider;
- cost avoided by local execution;
- throughput per compute hour;
- accepted work per dollar;
- first-pass accepted work per dollar;
- cost per validation pass.

## Audit and provenance requirements

Define an append-only event model that can reconstruct current state and history. Include events for creation, edits, structural changes, scheduling, staffing, assignment, capacity reservation, cost estimation, budget actions, dispatch, execution, blockers, retries, validation, acceptance, cancellation, archive, trash, restoration, branching, merge, and supersession.

Each event must identify:

- event ID and schema version;
- object type and object ID;
- actor and actor type;
- source surface or system;
- timestamp;
- prior and resulting state where applicable;
- reason;
- evidence and artifact references;
- conversation, room, file-import, work-package, dispatch, and validation references when applicable;
- correlation and causation IDs;
- integrity hash or chaining approach;
- classification and visibility.

Define current-state projections separately from the immutable event log.

## User surfaces

### Separate Project Management workspace

Specify a dedicated local Estate workspace with:

- Portfolio
- Projects
- Task Ledger
- Project outline/tree
- Board
- Dependency and branch graph
- Timeline and milestones
- Current Production
- Intake
- Dispatches
- Capacity and Utilization
- Financials
- Performance/KPIs
- Audit Timeline
- Archive/Trash
- Task and Project detail views

Task detail must surface Helen staffing evidence, Grace operational actions, Traffic Controller decisions, dispatch attempts, worker evidence, validation, financials, utilization, KPIs, and acceptance history.

### Office of the Steward integration

Do not add the full system to the existing Office page. Specify only a compact summary card and deep links such as:

- active projects;
- tasks in production;
- blocked work;
- awaiting Steward decision;
- recent completions;
- capacity available;
- 4090 utilization;
- month-to-date project cost;
- projects over budget;
- awaiting budget decisions;
- awaiting acceptance;
- open Project Management workspace;
- filtered links to blocked, production, intake, and decision views.

## Resident and authority integration

Specify governed hooks for relevant residents and offices to read and act on the same canonical objects shown in the Project Management workspace.

Include allowed command patterns, confirmation behavior, authority checks, audit events, and failure behavior. Conversational actions must never update a private side list disconnected from the canonical ledger.

## Existing Estate integration map

Inspect and map the design to existing Estate components including, at minimum:

- Office of the Steward navigation and command surfaces;
- Parking Lot and Roadmap controls;
- existing project/work-package views;
- resident conversations and conference room;
- Helen workforce artifacts;
- Grace operations runtime;
- Traffic Controller and Operations Control decisions;
- Execution Dispatch Queue;
- Engineering Worker Runtime bridge;
- validation and acceptance records;
- existing action-result logs, activity streams, and audit artifacts.

Identify which components should be reused, extended, projected into the new workspace, deprecated later, or left unchanged.

## Required outputs

Create the following specification artifacts:

1. `docs/architecture/estate_project_task_management_architecture.md`
   - complete conceptual architecture;
   - boundaries and authority model;
   - system-context diagram in Mermaid;
   - major data flow diagrams;
   - deployment/surface separation.

2. `docs/architecture/estate_project_task_management_protocol.md`
   - canonical object contracts;
   - lifecycle/state machines;
   - event protocol;
   - intake protocol;
   - scheduling, utilization, financial, KPI, audit, and acceptance protocols;
   - conversational command protocol;
   - soft-delete/archive/restore protocol.

3. `docs/architecture/estate_project_task_management_data_model.md`
   - field-level schemas or schema skeletons;
   - IDs and relationships;
   - current-state projections versus immutable events;
   - provenance and integrity strategy;
   - versioning and migration principles.

4. `docs/architecture/estate_project_task_management_user_experience.md`
   - dedicated workspace information architecture;
   - Office of the Steward compact card and deep links;
   - key screens, views, filters, and actions;
   - conversational examples;
   - accessibility and local-first considerations.

5. `docs/architecture/estate_project_task_management_kpi_financial_utilization_catalog.md`
   - KPI definitions and formulas;
   - utilization measures;
   - cost and budget measures;
   - required event/data sources;
   - baseline and target strategy;
   - data quality and unknown-value handling.

6. `docs/architecture/estate_project_task_management_implementation_roadmap.md`
   - implementation phases;
   - dependencies;
   - risks;
   - acceptance gates;
   - migration approach;
   - recommended pilot sequence.

7. `collaboration/work_packages/planning/estate_project_task_management_work_package_backlog.md`
   - numbered or placeholder work-package backlog grouped into logical categories;
   - each entry must include title, objective, dependencies, expected artifacts, suggested execution lane, and acceptance summary;
   - identify which packages are specification, core ledger, migration, UI, conversation integration, file intake, scheduling, utilization, financials, KPIs, audit, dispatch integration, testing, and rollout;
   - provide a recommended execution order;
   - packages may remain general where later refinement is required.

8. A completion receipt under `collaboration/work_packages/completions/` identifying files created, repository areas inspected, tests or document validation performed, known unknowns, and recommended first implementation work package.

## Required analysis questions

The specification must explicitly answer:

- What is the canonical source of truth?
- Is the event log append-only, and how are projections rebuilt?
- How are IDs assigned and preserved across import, split, merge, branch, and migration?
- What existing Estate records become references versus canonical objects?
- How are duplicate tasks and duplicate imports handled?
- How are soft delete, archive, trash, restore, and legal/audit retention distinguished?
- How do Helen and Grace actions become visible without exposing implementation noise?
- How are provider recommendations separated from authorized provider selection?
- How are scheduling, capacity, budget, and privacy gates enforced before Dispatch becomes Ready?
- How are local and external execution costs estimated and reconciled?
- How are KPIs protected from missing, stale, or manipulated data?
- How does the workspace remain usable with thousands of tasks and long histories?
- How are project branches represented without turning the hierarchy into an unreadable tree?
- What is the smallest safe pilot that proves the architecture?

## Validation

At minimum:

- verify all required files exist;
- validate Mermaid blocks syntactically where repository tooling permits;
- check internal links and referenced repository paths;
- confirm no implementation code or second execution path was introduced;
- confirm the roadmap and backlog cover every mandatory domain in this package;
- run existing documentation or work-package validation tools where applicable.

## Acceptance criteria

This package is complete only when:

- all required documents exist and are internally consistent;
- the architecture clearly separates Project, Task, Work Package, Dispatch, Evidence, Validation, and Acceptance;
- audit, scheduling, branching, utilization, financials, KPIs, intake, resident access, and UI separation are first-class;
- existing Estate components are mapped and reused rather than duplicated;
- the Office of the Steward remains a compact summary/link surface;
- the dedicated Project Management workspace is fully specified;
- the implementation roadmap contains a practical, sequenced backlog of future work packages;
- no production implementation is performed in this package;
- a PR is opened for Chief Architect review and is not merged by Codex.
