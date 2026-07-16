# WP-0666 — EOC/CME Operational Policy, Blocker, Notification, and Escalation Model

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Change class: Architecture and planning only  
Campaign: EOC-CME-ARCH-01  
Depends on: WP-0663, WP-0664, WP-0665

## Objective

Define the policy model that lets the Continuous Momentum Engine identify the highest-value authorized next transition, recover from ordinary operational blockers, and escalate only genuine authority blockers while remaining explainable, bounded, and constitutionally subordinate.

## Required Inputs

- accepted EOC/CME architectural charter;
- WP-0663 through WP-0665 deliverables;
- PTM priorities, readiness gates, dependencies, critical-path, and scheduling rules;
- Grace operations-runtime evidence;
- staffing and capacity evidence;
- validation and operational-readiness evidence;
- current notification, escalation, and blocker conventions.

## Required Work

### 1. Policy representation

Define a versioned, reviewable policy contract containing:

- policy identity and version;
- authority source;
- applicable operational mode;
- scope and exclusions;
- required observations;
- eligibility predicates;
- prohibited transitions;
- priority and tie-break rules;
- bounded retry and recovery rules;
- notification behavior;
- escalation threshold;
- effective and expiration times;
- evidence and audit requirements.

Policies must be declarative where practical, deterministic under the same evidence, and incapable of granting authority not already present.

### 2. Momentum evaluation model

Define how eligible transitions are collected, filtered, scored, compared, and selected.

The evaluation must account for:

- authorization;
- readiness;
- dependencies;
- critical path;
- initiative priority;
- staffing and capacity;
- validation status;
- blocker age and severity;
- operational health;
- risk of delay;
- fairness and starvation prevention;
- Steward availability only where a protected decision is actually required.

The model must not use an opaque scalar score as the sole justification. It must produce a structured explanation of included candidates, excluded candidates, selected transition, policy clauses, evidence, and tie-breaks.

### 3. Blocker taxonomy

Define canonical blocker classes at minimum:

- workforce unavailable;
- capability unavailable;
- dependency unresolved;
- validation failed;
- validation recipe missing;
- integration conflict;
- compute or service capacity;
- degraded service;
- stale evidence;
- ambiguous identity or state;
- architectural change required;
- strategic priority conflict;
- constitutional boundary;
- privacy or security authority;
- budget authority;
- legal authority;
- final acceptance required.

For each class specify operational vs authority classification, owner, evidence, permitted recovery actions, retry limits, aging policy, escalation condition, and terminal outcomes.

### 4. Notification policy

Define when the Estate should:

- record silently;
- surface to Grace;
- notify an office;
- request acknowledgment;
- notify the Steward;
- suppress duplicates;
- update an existing notification;
- close or expire a notification.

Notifications must be stateful, deduplicated, severity-aware, evidence-linked, and resistant to alert storms.

### 5. Escalation policy

Define protected escalation packages that include:

- concise decision requested;
- why delegated authority is exhausted;
- evidence and current state;
- options considered;
- recommended option and consequences;
- deadline or operational impact;
- affected campaigns and offices;
- safe hold state while awaiting decision.

### 6. Pause, hold, retry, and recovery

Define the legal distinction among pause, hold, retry, reassignment, bounded rework, campaign replan, and termination. Specify which actions Grace may coordinate, which office decides, and what evidence must be preserved.

## Deliverables

Create:

1. `docs/architecture/eoc_cme_operational_policy_model.md`
2. `docs/architecture/eoc_cme_momentum_evaluation_and_explanation_rules.md`
3. `docs/architecture/eoc_cme_blocker_taxonomy.md`
4. `docs/architecture/eoc_cme_notification_policy.md`
5. `docs/architecture/eoc_cme_escalation_policy.md`
6. `docs/architecture/eoc_cme_pause_hold_retry_and_recovery_model.md`
7. `collaboration/work_packages/completions/WP-0666_completion_receipt.md`

## Non-Goals

- no self-modifying policy;
- no machine-learned authority inference;
- no implementation of a scheduler;
- no automatic architecture, budget, privacy, legal, or acceptance decisions;
- no alerting system replacement;
- no unbounded retries.

## Validation

- identical evidence and policy produce deterministic eligibility and selection;
- every selected transition has a complete explanation;
- every excluded candidate has an explicit reason;
- operational blockers never silently cross into protected authority;
- protected blockers always fail closed and generate a bounded escalation package;
- duplicate events do not create duplicate notifications or actions;
- retry and recovery rules are bounded and auditable;
- starvation and policy-conflict behavior are explicitly defined.

## Acceptance Criteria

The policy suite must permit continuous operational movement without hiding why work advanced, why it stopped, or who holds the authority required to continue.

## Delivery

Open a pull request for Chief Architect review. Do not merge. Do not implement runtime behavior.