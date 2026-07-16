# WP-0674 — Engineering Operations Metrics, Notebook, and Continuity Integration

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Campaign: CAMPAIGN-0670 Engineering Department Operationalization  
Depends on: WP-0670, WP-0671, WP-0672

## Objective

Create the Engineering Department operational visibility and continuity model so campaign state, decisions, evidence, risks, worker transitions, and architectural context remain durable across workers, models, reflections, and time.

This package must integrate with existing Estate boards, work-package records, mailbox/message systems, engineering notebook practices, reflection/continuity procedures, PTM state, and operational reporting. It must not create a second status registry or a private shadow workflow.

## Required Inputs

Review at minimum:

- `operations/departments/engineering/engineering_department_charter.md`
- `operations/departments/engineering/engineering_department_operating_guide.md`
- outputs from WP-0670, WP-0671, and WP-0672
- `AI_HINTS.md` and communication/continuity quick-reference files
- `docs/operations/ChatGPT_Worker_Reflection_and_Continuity_Process_v1.md`
- `docs/templates/ChatGPT_Worker_Reflection_Continuity_Template_v1.md`
- current Engineering Notebook or equivalent decision-record locations
- PTM campaign, package, dependency, utilization, and KPI contracts
- current Daily Board, Active Work, parking-lot, mailbox, message, and completion-receipt conventions
- existing Grace, Helen, Alfred, Chief Architect, and Steward operational surfaces

## Required Work

### 1. Engineering campaign status model

Define one canonical operational view for every engineering campaign and package, including:

- campaign and package IDs;
- current lifecycle state;
- owner and responsible office;
- execution lane and provider;
- readiness and dependency state;
- branch, PR, and integration state;
- validation and acceptance state;
- blocker classification and age;
- next authorized action;
- evidence links;
- last material transition and timestamp;
- continuity and reflection status.

Identify which existing artifact is authoritative for each field. Derived views may aggregate but may not become competing sources of truth.

### 2. Engineering Notebook integration

Define the Engineering Notebook as a durable architectural and execution-memory surface, not a second work queue. Specify entries for:

- architectural decisions and rejected alternatives;
- contract freezes;
- implementation discoveries;
- integration hazards;
- provider behavior and qualification evidence;
- validation anomalies;
- deferred work and parking-lot links;
- operational lessons;
- campaign closure observations.

Every entry must reference the related campaign, package, commit, PR, message, or evidence record.

### 3. Operational metrics

Define metrics with formulas, source records, and interpretation boundaries for:

- campaign throughput;
- package cycle time;
- queue and readiness latency;
- implementation time;
- validation latency;
- integration latency;
- rework rate;
- blocker age and recovery time;
- provider success and failure rate;
- Codex versus local execution utilization;
- stale package count;
- orphaned branch or PR count;
- continuity handoff frequency;
- reflection-trigger frequency;
- Steward interruption rate;
- percentage of campaign transitions completed without Steward scheduling.

Metrics provide operational evidence only. They may not silently determine authority, acceptance, staffing, or priority.

### 4. Reporting surfaces

Specify bounded reporting for:

- Grace operational campaign view;
- Chief Architect engineering portfolio view;
- Helen staffing demand and capability-shortage view;
- Alfred routing and unresolved communication view;
- Steward executive summary;
- individual campaign detail;
- package drill-down;
- blocker and risk aging;
- provider performance evidence.

Reuse existing command surfaces, dashboards, boards, and registries wherever possible.

### 5. Communication integration

Define when engineering uses:

- repository messages;
- mailbox discovery;
- campaign records;
- work-package comments or receipts;
- Daily Board and Active Work updates;
- parking-lot capture;
- Chief Architect acceptance communication;
- Steward escalation.

The package must include copy-ready communication patterns and must align with `AI_COMMUNICATION_HINTS.md` or its canonical successor.

### 6. Reflection and continuity integration

Define mandatory continuity behavior for:

- context congestion;
- worker replacement;
- Chief Architect reflection point;
- long-running campaign handoff;
- provider failure mid-package;
- branch or PR ownership transfer;
- interrupted validation;
- unresolved authority blocker.

Specify when a worker must create a reflection package, execution handoff addendum, renewal/pilot record, or simple bounded handoff. Preserve the master reflection-process document as authoritative.

### 7. Staleness and reconciliation

Define reconciliation checks for discrepancies among campaign records, Pending packages, PRs, branches, completion receipts, validation reports, boards, messages, and runtime projections. Stale or contradictory state must be visible and fail closed.

## Deliverables

Create or update:

1. `docs/operations/Engineering_Campaign_Operational_Status_Model_v1.md`
2. `docs/operations/Engineering_Notebook_Integration_Standard_v1.md`
3. `docs/operations/Engineering_Metrics_and_Reporting_Model_v1.md`
4. `docs/operations/Engineering_Communication_and_Escalation_Standard_v1.md`
5. `docs/operations/Engineering_Reflection_and_Continuity_Integration_v1.md`
6. any required quick-reference pointer updates
7. CAMPAIGN-0670 operational dashboard/status specification
8. `collaboration/work_packages/completions/WP-0674_completion_receipt.md`

## Non-Goals

- no second registry;
- no second scheduler or queue;
- no replacement for PTM;
- no private worker-only status store;
- no new constitutional authority;
- no automatic priority decisions from metrics;
- no replacement of the canonical reflection process;
- no implementation of unrelated product features.

## Validation

Before claiming completion, verify that:

- every displayed field has one named authoritative source;
- derived views cannot overwrite canonical state;
- Notebook entries link to durable evidence;
- metrics have explicit formulas and source records;
- communication routing follows existing mailbox/message rules;
- continuity artifacts are triggered by defined conditions;
- a fresh Chief Architect can recover campaign state without relying on chat history;
- no duplicate queue, registry, or governance path was introduced.

## Acceptance Criteria

The Engineering Department must be able to preserve truthful campaign state, architectural memory, operational metrics, communication history, and execution continuity across worker turnover and context rollover while using existing Estate systems as authoritative sources.

## Delivery

Open a pull request for Chief Architect review. Do not merge. Include validation evidence and create the required completion receipt.