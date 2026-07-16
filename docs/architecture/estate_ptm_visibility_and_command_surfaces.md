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

### Workspace navigation model

The workspace shell must use a single left-navigation hierarchy for the seven sections above and must not create a second task queue, registry, scheduler, or authority surface. Global search may jump to portfolio, project, task, intake, audit, archive, and trash routes, but search results remain read-only navigation affordances until a governed command handler opens a confirmation envelope.

Required shell regions are:

- a persistent section rail containing Portfolio, Projects, Task Ledger, Intake, Audit, Archive, and Trash;
- a contextual header showing the active route ID, projection freshness, hash/rebuild status, and any blocked governance gate;
- a primary content pane optimized for the selected projection-backed table, board, timeline, or detail view;
- a secondary inspector that can summarize links, evidence, route targets, and command results without mutating canonical state;
- a footer/status strip for validation state, acceptance separation, and source evidence warnings when applicable.

### Section relationships and default entry points

| From section | Default drill-down target | Cross-navigation rule |
|---|---|---|
| Portfolio | Filtered `ptm.projects` by portfolio or health segment | Portfolio metrics link to project/task filters, not duplicate portfolio-owned ledgers |
| Projects | `ptm.projects.detail` for the selected `PROJ-` ID | Project rows may open task filters, audit timelines, or command confirmations |
| Task Ledger | `ptm.tasks.detail` for the selected `TASK-` ID | Ledger rows remain canonical task navigation; bulk selection cannot bypass governed handlers |
| Intake | Candidate detail or duplicate review panel | Confirmed candidates navigate to canonical project/task targets; rejected candidates remain auditable |
| Audit | Object-scoped event timeline | Audit may link back to object details but remains read-only except governed annotation events |
| Archive | Prior project/task route target | Restore actions open confirmation; archive never becomes a second active workspace |
| Trash | Prior project/task route target with retention/hold status | Purge-block and restore visibility stays governed and auditable |

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

### Projection binding map

All workspace bindings consume the CORE-PTM-003A and CORE-PTM-003B projection names as read models. UI implementations may rename labels for display, but they must not rename, reinterpret, or silently coerce the source projection fields listed below.

| Workspace target | Canonical projection records | Required primary keys | Required quality/status fields | Required navigation targets |
|---|---|---|---|---|
| `ptm.portfolio` | `portfolio.current_state`, `financial.current_state`, `kpi.observation` | `portfolio_id`, `project_ids`, `task_ids` | projection envelope `stale`, `warnings`, `high_watermark_event_id`; KPI `quality_label` and `publication_state`; financial `budget_ready` and `authority_warnings` | filtered `/office/ptm#projects`, `/office/ptm#tasks`, `/office/ptm#blocked`, `/office/ptm#decisions` |
| `ptm.projects` | `project.current_state`, `task.current_state`, `schedule.current_state`, `financial.current_state` | `project_id`, related `task_ids`, milestone IDs where present | normalized status, schedule readiness, budget state, acceptance wait counts, projection warnings | `/office/ptm#project/<PROJ-id>`, filtered `/office/ptm#tasks`, object audit route |
| `ptm.projects.detail` | `project.current_state`, linked task/schedule/financial/KPI/audit records | requested `PROJ-` ID retained even when missing | missing/unknown projection state, source confidence, freshness, hash/rebuild state | prior section route, task filters, `/office/ptm#audit/<object-id>` |
| `ptm.task_ledger` | `task.current_state`, `task.status_rollup`, `schedule.current_state`, `financial.current_state`, `audit.event_trace` | `TASK-` ID, `project_ids`, `branch_ids`, `WP-`/`DISP-` links where present | blocker, dispatch, validation, acceptance, classification, evidence completeness, stale/warning labels | `/office/ptm#task/<TASK-id>`, filtered production/blocked/decision routes |
| `ptm.tasks.detail` | `task.current_state`, relationship index, schedule/financial/utilization/KPI/audit records | requested `TASK-` ID retained even when missing | governed gate outcomes, acceptance separation, evidence warnings, projection freshness | project detail, branch/work-package/dispatch evidence links, object audit route |
| `ptm.intake` | `intake_projection`, `task.current_state`, `audit.event_trace` | `INTAKE-` ID, duplicate candidate `TASK-`/`PROJ-` IDs | confirmation state, duplicate confidence, source hash, classification/visibility warnings | confirmed canonical target, duplicate review, `/office/ptm#intake` |
| `ptm.audit` | `audit.event_trace` | event ID, object ID, causation/correlation IDs | hash status, projection rebuild state, evidence refs, actor/source warnings | object detail route and immutable evidence references |
| `ptm.archive` / `ptm.trash` | filtered `project.current_state`, `task.current_state`, `branch_graph`, `audit.event_trace` | object ID and prior route target | archived/trashed timestamp, hold state, restore eligibility, purge-block reason | prior project/task route, restore confirmation, object audit route |

### Large-ledger navigation contract

The Task Ledger and any project-filtered task table are expected to grow beyond in-memory browser rendering. Future UI files must therefore implement navigation against cursor-backed projection slices rather than loading every task row at once. The stable cursor contract is:

- cursor inputs: route ID, projection name, projection version, high-watermark event ID, stable sort key, filter expression, page size, and opaque cursor token;
- default stable sort: `updated_at` descending, then canonical ID ascending, with alternate sorts limited to explicit projection fields;
- cursor outputs: row records, next/previous opaque cursor tokens, current high-watermark event ID, total count only when available without unbounded replay, and projection warning summaries;
- URL state: section, detail target, filters, sort key, page size, and cursor token may be represented in the URL so browser back/forward restores navigation without reminting IDs or reissuing commands;
- selection state: bulk selection is page- and filter-scoped UI state only until a governed command handler creates a confirmation envelope;
- missing rows: if a cursor points at a row that is no longer visible because a projection advanced, the UI must show an honest stale-cursor notice and offer refresh/navigation, not fabricate a task state.

### Missing, stale, and partial projection states

Every route must explicitly render projection quality instead of flattening uncertainty into normal values. Required states are:

- `missing`: the requested canonical ID is well-formed but absent from the current projection; show the ID, route target, and an audit lookup affordance;
- `unknown`: the projection contract allows the field to be unavailable; show `Unknown` with the source warning or missing-evidence reason;
- `stale`: the projection envelope or a joined domain record marks stale input; show the high-watermark and refresh/rebuild status;
- `partial`: joined projection families disagree or have different high-watermarks; show the affected families and suppress derived KPI/financial conclusions when required by the projection contracts;
- `blocked_by_governance`: a route or command result depends on staffing, budget, validation, acceptance, Traffic Controller, Helen, Grace, Steward, or Chief Architect gates that have not been satisfied.

### Detail route contract

Detail routes must be deterministic functions of the canonical ID and current projection high-watermark. Opening `/office/ptm#task/<TASK-id>` or `/office/ptm#project/<PROJ-id>` must not emit events, enqueue dispatch, infer acceptance, create private lists, or mutate schedule state. Detail views may open command confirmations, but the confirmation envelope remains the only mutation path.

Project detail views must show project summary, linked task rollups, schedule readiness, budget/financial warnings, KPI quality, milestone state, source evidence, and audit timeline. Task detail views must show task summary, project/branch relationships, staffing readiness, Grace operational evidence, Traffic Controller routing decisions, dispatch evidence, validation and acceptance separation, financial/utilization/KPI observations, source artifacts, and audit timeline.

### Gate C downstream implementation checks

A future Office UI implementation package satisfies this UI-PTM-001B contract only when it demonstrates that:

1. all rendered PTM values originate from named projections or immutable evidence references;
2. all deep links use the frozen target list or a Gate C-approved extension;
3. large-ledger tables use cursor pagination or virtualization with stable URL restoration;
4. command-result navigation returns governed route targets and never directly mutates state from client filter or selection state;
5. missing, stale, partial, and unknown projection states are visible to the user; and
6. no second queue, second registry, second scheduler, private task list, or new governance authority is introduced.

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

### Summary data contract

The compact card consumes the same projection-backed bindings frozen for the workspace and may cache only display summaries derived from those projections. A future card implementation must treat the following values as read-model inputs, not as Office-owned task state:

| Card zone | Required projection/evidence source | Required quality label | Allowed deep-link target |
|---|---|---|---|
| Portfolio summary | `portfolio.current_state`, `project.current_state`, `task.status_rollup` | projection freshness and active-count confidence | `/office/ptm#portfolio`, `/office/ptm#projects` |
| Production strip | `task.current_state`, `schedule.current_state`, dispatch evidence where present | schedule readiness and dispatch readiness | `/office/ptm#production`, `/office/ptm#tasks` |
| Blockers and decisions | `task.current_state`, `schedule.current_state`, financial authority warnings, validation/acceptance state | blocker stale/unknown label and named gate owner | `/office/ptm#blocked`, `/office/ptm#decisions` |
| Intake health | `intake_projection` and duplicate review state | backlog age, duplicate confidence, and source warning label | `/office/ptm#intake` |
| Cost/capacity health | `financial.current_state`, utilization observations, 4090 telemetry if available | unknown/stale/estimated labels and budget authority boundary | `/office/ptm#portfolio`, filtered project links |
| Evidence freshness | `audit.event_trace`, projection envelope, hash/rebuild status | hash-chain/rebuild status and high-watermark event ID | `/office/ptm#audit/<object-id>` where object-scoped |

### Display and interaction rules

- The card must fit a compact Office dashboard slot and expose at most a short list of top projects or task alerts; it must link to the workspace for tables, boards, timelines, details, filters, audit history, and command workflows.
- Counts and chips must preserve `missing`, `unknown`, `stale`, `partial`, and `blocked_by_governance` states defined by UI-PTM-001B instead of converting them to zero, healthy, or accepted values.
- The card may rank top active projects by priority only when priority is present in the projection; otherwise it must show an unknown-priority label and link to the filtered workspace.
- Task, project, intake, cost, capacity, and evidence labels must include enough context for a Steward to choose the correct deep link, but raw event payloads and long task ledgers stay in the workspace.
- The card must not store user-created watchlists, hidden task lists, alternate project IDs, Office-local dispatch states, or Office-local acceptance/validation decisions.

### Compact card actions

Allowed Office card actions are navigation-only or confirmation-opening actions that delegate to governed handlers. The card may open PTM workspace links, open filtered blocked/production/intake/decision views, or open an existing governed confirmation surface. It must not directly mutate project/task state without the same command envelope, confirmation, and eventing used by the full workspace.

| User action | Allowed behavior | Prohibited behavior |
|---|---|---|
| Open portfolio/project/task summary | Navigate to one of the frozen workspace route targets with filters encoded as URL state | Render a full project/task workspace inside Office card |
| Review blocker or decision chip | Navigate to `/office/ptm#blocked`, `/office/ptm#decisions`, or object detail/audit route | Mark blocker resolved, approve budget, validate, or accept from card state |
| Open intake backlog | Navigate to `/office/ptm#intake` or an existing governed confirmation surface | Create an Office-local candidate list or bypass dedupe confirmation |
| Open production status | Navigate to `/office/ptm#production` or task detail | Move work into production, dispatch work, or change schedule readiness directly |
| Start a governed command | Open the same canonical confirmation envelope used by workspace or Resident commands | Mint IDs, mutate tasks, or enqueue dispatch from card-only handlers |

### Deep-link payload requirements

Every card link must use a frozen target from UI-PTM-001A/UI-PTM-001B and include only navigation state: target route, canonical object ID where applicable, optional filter chips, cursor/sort/page state when returning to a table, source surface `office_compact_card`, and projection high-watermark. Deep links must not carry authoritative command intent, hidden approvals, Office-local IDs, or acceptance/validation outcomes.

### Future implementation validation checklist

A future Office card implementation satisfies this contract only when validation demonstrates that:

1. the card renders summary counts/chips from named PTM projections or immutable evidence references;
2. every card link resolves to the frozen workspace deep-link list or a Gate C-approved extension;
3. no card view renders an unbounded ledger, board, audit timeline, or detail workspace;
4. every mutating affordance opens the canonical governed confirmation envelope and does not mutate from card state;
5. missing, unknown, stale, partial, and governance-blocked states remain visible; and
6. no second queue, second registry, second scheduler, private Office task list, budget authority, validation authority, acceptance authority, or governance authority is introduced.

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

### Command confirmation and result contract

Future Resident command files must implement confirmations as thin, governed envelopes over canonical PTM handlers. The command surface may draft a confirmation, render a denial, or return read-only history, but it must not mint PTM IDs, write task state, change schedule readiness, assign Helen/Grace authority, move dispatch work, or approve budgets outside the frozen upstream contracts.

| Command family | Pre-confirmation checks | Confirmation payload | Confirmed result | Denial or blocked result |
|---|---|---|---|---|
| Create | Intake dedupe, target project existence or Parking Lot fallback, classification, source evidence hash, and visibility | Proposed intake/task title, target project or Parking Lot, duplicate candidates, evidence refs, classification, reason, route targets | Append intake/create event through governed intake; return `INTAKE-` or `TASK-` ID and `/office/ptm#intake` or task detail link | Return duplicate candidates, missing evidence, or classification warning without creating a task |
| Link | Source and target object existence, relationship type validity, duplicate link, permissions, and evidence | Source object, target object, proposed relationship, evidence refs, warnings, route targets | Append relationship event; return affected IDs and task/project/audit links | Return missing target, duplicate relationship, or permission warning |
| Priority | Current priority, requested priority, reason, schedule/budget impact, blocker/acceptance state | Current and proposed priority, reason, impact warnings, evidence refs, route targets | Append priority-change event; return updated priority and schedule warning summary | Return missing reason, invalid priority, or blocked authority gate |
| Production | Staffing readiness, schedule gate, capacity, budget status, privacy/classification, validation plan, acceptance owner | Target task, current state, required gate outcomes, evidence refs, production route, blocked route | Append production-state request/change only when all gates pass; return production and task links | Return named failed gates with evidence links; do not move work into production |
| Helen | Task existence, staffing-readiness scope, evidence sufficiency, budget/dispatch/acceptance boundary | Staffing request/evidence summary, Helen scope note, evidence refs, route targets | Append staffing-readiness request/evidence event; return task and audit links | Return missing scope/evidence or authority-boundary warning |
| Grace | Staffing readiness already present, operational supervision scope, Traffic Controller routing boundary | Grace request/evidence summary, staffing readiness link, authority-boundary note, route targets | Append operational supervision request/evidence event; return task and audit links | Return missing staffing readiness or Traffic Controller boundary warning |
| History | Object ID namespace and projection availability | No material confirmation required for read-only history | Render audit timeline with evidence links, hash-chain status, projection freshness, and object route | Return honest missing/unknown projection state with retained object ID and audit link |

All material results must include the event ID or pending confirmation ID, affected object IDs, source evidence refs, validation/acceptance separation note when applicable, and one or more frozen deep-link targets. Read-only history results must disclose projection freshness and hash-chain status rather than implying mutation.

## Gate C reconciliation evidence

This PTM-04 artifact preserves frozen upstream event, ID, projection, intake, route, schedule, dispatch, and validation contracts. It defines route and command consumers only. Future implementation packages must reconcile against this document before creating Office UI files, resident command files, or compact-card files.
