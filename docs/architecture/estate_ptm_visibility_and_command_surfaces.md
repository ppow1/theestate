# Estate PTM Visibility and Command Surfaces

Status: implementation-ready planning artifact for PTM-04. Change class: architecture/specification only.

## Authority and scope

This document executes PTM-04 planning packages UI-PTM-001A, UI-PTM-001B, UI-PTM-002, and CONV-PTM-001 by freezing the first Project Task Management workspace route and command-surface contract for later implementation. It is source-backed by the accepted PTM baseline and does not introduce production PTM code, a second queue, a second registry, a second scheduler, or new governance authority.

The canonical source of truth remains the append-only PTM event log and immutable referenced evidence. Workspace tables, Office cards, route summaries, command confirmations, and navigation counts are projections or views over frozen upstream contracts.

## UI-PTM-001A workspace information architecture shell

The dedicated Project Management workspace owns the full planning interface. The Office of the Steward only receives summary cards and deep links.

### Top-level workspace sections

| Section | Route ID | Purpose | Default projection source | Mutability |
|---|---|---|---|---|
| Portfolio | `ptm.portfolio` | Estate-wide portfolio health, active/blocked/completing project groups, and portfolio-level risk | `project_current`, `financial_projection`, `kpi_observation_projection` | Read/write only through governed project handlers |
| Projects | `ptm.projects` | Project list, project detail, project outline/tree, board, current production view, and milestone rollups | `project_current`, `task_current`, `task_relationship_index`, `schedule_projection` | Governed project/task handlers |
| Task Ledger | `ptm.task_ledger` | Large canonical task table with filters, saved views, bulk-safe navigation, and evidence completeness | `task_current`, `audit_timeline`, `branch_graph` | Governed task handlers only |
| Intake | `ptm.intake` | Manual, Parking Lot, conversation, and file-import candidates awaiting confirmation or dedupe review | `intake_projection`, `task_current` | Intake confirmation handlers |
| Audit | `ptm.audit` | Append-only event timeline, evidence references, hash-chain/projection rebuild status, and acceptance separation | `audit_timeline` | Read-only except governed annotation events |
| Archive | `ptm.archive` | Archived portfolios, projects, tasks, branches, and completed historical work hidden from default active views | `project_current`, `task_current`, `branch_graph` filtered by archived state | Restore events only |
| Trash | `ptm.trash` | Reversible removals with retention, legal/audit hold, and purge prohibition visibility | `task_current`, `project_current`, `audit_timeline` filtered by trashed state | Restore or governed purge-block annotation only |

### Detail surfaces

Every `ptm.projects.detail` and `ptm.tasks.detail` view must disclose summary first and defer raw runtime detail behind expansion controls. Detail views show project links, branch graph, relationships, Helen staffing evidence, Grace operational actions, Traffic Controller decisions, dispatch attempts, worker evidence, validation, acceptance, financials, utilization, KPI observations, source artifacts, and audit events.

### Deep-link target freeze

Future Office cards and Resident responses may link only to these route targets unless a Gate C reconciliation explicitly extends the contract:

- `/office/ptm#portfolio`
- `/office/ptm#projects`
- `/office/ptm#tasks`
- `/office/ptm#task/<TASK-id>`
- `/office/ptm#project/<PROJ-id>`
- `/office/ptm#intake`
- `/office/ptm#audit/<object-id>`
- `/office/ptm#archive`
- `/office/ptm#trash`
- `/office/ptm#production`
- `/office/ptm#blocked`
- `/office/ptm#decisions`

## UI-PTM-001B data binding and navigation contract

### Projection-backed bindings

The workspace must render from rebuildable projections and retain links to canonical event/evidence artifacts:

| View | Required bindings | Large-ledger behavior |
|---|---|---|
| Portfolio | portfolio ID, project counts by state, cost variance, KPI confidence, blocked/completing summaries | Aggregate cards link into filtered project/task views |
| Projects | project ID, title, status, priority, owner, budget state, milestone state, active task counts, acceptance wait counts | Cursor pagination and saved filters; no unbounded render |
| Task Ledger | task ID, title, status, priority, project IDs, branch IDs, owner/resident, Helen readiness, Grace state, blocker, dispatch state, validation state, acceptance state, classification, evidence completeness | Virtualized table, cursor pagination, stable sort key, and filter chips reflected in URL |
| Intake | intake ID, source type, title, duplicate candidates, confirmation state, source hash, warnings, target project/task | Confirmation opens governed intake handlers; rejected items remain auditable |
| Audit | event ID, object ID, event type, actor, timestamp, causation/correlation IDs, evidence refs, hash status, visibility | Timeline is paginated by object and timestamp |
| Archive/Trash | object ID, prior route target, archived/trashed timestamp, hold state, restore eligibility | Default hides purged-ineligible details behind hold explanations |

### Route parameter and URL rules

- Route parameters must preserve canonical PTM namespaces: `PORT-`, `PROJ-`, `TASK-`, `BRANCH-`, `WP-`, `DISP-`, `INTAKE-`, `KPI-`, and `COST-`.
- Detail routes must show an honest missing/unknown state when the projection is absent while retaining the requested ID in the page title and audit link.
- Filter state may be encoded in query parameters, but commands must not trust client filters as authority.
- Browser back/forward must restore section, detail target, filters, and page cursor without reminting IDs or reissuing commands.

### Command navigation responses

Any command that creates, links, reprioritizes, moves, archives, restores, or requests staffing/operations must return a command result containing: event ID or pending confirmation ID, affected object IDs, resulting state summary, evidence refs, validation/acceptance separation note when relevant, and one or more route targets from the frozen deep-link list.

## UI-PTM-002 Office compact card and deep-link contract

The Office compact card is summary-only. It must not duplicate the full Project Management workspace, render large ledgers, expose private side lists, or create an alternate project/task control surface.

### Compact card content

The Office card may show only:

- active project count and top active projects by priority;
- tasks in current production;
- blocked tasks and stale blocker counts;
- tasks awaiting Steward decision, budget decision, validation, or acceptance;
- recent completions;
- capacity availability and utilization summary, including 4090 utilization when telemetry is available;
- month-to-date PTM cost, over-budget project count, and unknown-cost count;
- health chips for projection freshness, intake backlog, dispatch readiness, and evidence completeness;
- deep links to filtered workspace targets.

### Compact card actions

Allowed Office card actions are navigation-only or confirmation-opening actions that delegate to governed handlers. The card may open PTM workspace links, open filtered blocked/production/intake/decision views, or open an existing governed confirmation surface. It must not directly mutate project/task state without the same command envelope, confirmation, and eventing used by the full workspace.

## CONV-PTM-001 resident governed PTM command contract

Resident commands are governed front doors into the canonical PTM event system. They do not create private resident task lists or bypass intake, staffing, budget, dispatch, validation, or acceptance authorities.

### Supported command families

| Command family | Example intent | Required confirmation/result behavior |
|---|---|---|
| Create | "Create a task from this discussion" | Propose title, target project or Parking Lot/intake state, classification, evidence refs, duplicate hints, and ask for confirmation before material eventing |
| Link | "Add this to PROJ-0001" or "Link this to TASK-0007" | Show target object, relationship type, source evidence, duplicate/permission warnings, and confirmation |
| Priority | "Change priority to high" | Show current and proposed priority, reason, affected schedule/budget warnings, and confirmation |
| Production | "Move TASK-0007 into current production" | Check staffing, schedule, capacity, budget, privacy/classification, validation plan, and acceptance-owner gates; return blocked evidence or confirmation |
| Helen | "Helen assess staffing for TASK-0007" | Create or link staffing-readiness request/evidence without assigning budget, dispatch, or acceptance authority |
| Grace | "Grace take TASK-0007 after staffing readiness" | Create operational supervision request/evidence only after staffing readiness; Traffic Controller remains routing/movement authority |
| History | "Show full history of TASK-0007" | Render audit timeline from projections/events without mutation; include evidence links and hash/projection status |

### Confirmation envelope

Material command confirmations must include: command family, actor, actor type, source surface, target object IDs, proposed event type, prior/resulting state summary, reason, evidence refs, classification/visibility, duplicate warnings, governance gate outcomes, frozen deep-link targets, and expiration. Confirmed commands emit append-only events using upstream command and event contracts; denied/expired commands remain visible as audit/intake evidence where appropriate.

## Gate C reconciliation evidence

This PTM-04 artifact preserves frozen upstream event, ID, projection, intake, route, schedule, dispatch, and validation contracts. It defines route and command consumers only. Future implementation packages must reconcile against this document before creating Office UI files, resident command files, or compact-card files.
