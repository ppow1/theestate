# Estate Project and Task Management User Experience

## Dedicated workspace information architecture

Workspace sections: Portfolio, Projects, Task Ledger, Project outline/tree, Board, Dependency and branch graph, Timeline and milestones, Current Production, Intake, Dispatches, Capacity and Utilization, Financials, Performance/KPIs, Audit Timeline, Archive/Trash, and Task/Project detail.

Task detail surfaces summary, project links, branch graph, relationships, Helen staffing evidence, Grace operational actions, Traffic Controller decisions, dispatch attempts, worker evidence, validation, financials, utilization, KPIs, acceptance history, audit events, and source artifacts. Raw runtime noise is behind disclosure controls.

## Office compact card

The Office of the Steward shows only active projects, tasks in production, blocked work, awaiting Steward decision, recent completions, capacity available, 4090 utilization, month-to-date project cost, projects over budget, awaiting budget decisions, awaiting acceptance, and links to the Project Management workspace plus filtered views for blocked, production, intake, and decisions.

## Key filters and actions

Filters: portfolio, project, status, priority, owner, resident, Helen readiness, Grace state, blocker, branch, due date, budget state, validation state, acceptance state, provider, classification, stale ownership, and missing evidence. Actions use governed handlers and confirmations for material change.

## Conversational examples

- Resident: “Create a task from this discussion.” System replies with proposed title, project, classification, evidence link, and confirmation request.
- Steward: “Move TASK-0007 into current production.” System checks staffing, schedule, capacity, budget, privacy, and validation gates before eventing the change.
- Helen: “Assess staffing for TASK-0007.” Result links staffing evidence without assigning budget or dispatch authority.
- Grace: “Take TASK-0007 after staffing readiness.” Result creates operational supervision events and may request Traffic Controller decision.
- Any authorized reader: “Show full history of TASK-0007.” System renders audit timeline from events and evidence.

## Accessibility and local-first

Use keyboard-accessible boards, graph alternatives as tables, reduced-motion timeline, semantic headings, high-contrast statuses, saved filters, paginated/virtualized lists, offline-readable projections, and honest unknown states when local artifacts are missing.

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
