# WP-0667 — EOC/CME Momentum Evaluation, Explainability, and Operational Observability

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Change class: Architecture and planning only  
Campaign: EOC-CME-ARCH-01  
Depends on: WP-0663, WP-0664, WP-0665, WP-0666

## Objective

Define the policy-driven momentum evaluation model, recommendation scoring, explanation contract, operational metrics, and observability surfaces required for Grace and the Steward to understand why the Estate recommends a next transition without granting the evaluator independent authority.

## Required Inputs

- `docs/architecture/estate_operations_center_continuous_momentum_engine_architectural_charter.md`;
- all accepted outputs from WP-0663 through WP-0666;
- PTM scheduling, dependency, utilization, financial, and KPI contracts;
- Grace operational runtime and Office command surfaces;
- validation reconciliation and operational-readiness closure records;
- staffing availability and capacity evidence;
- notification and escalation policy;
- existing Estate status, dashboard, and evidence-link conventions.

## Required Work

### 1. Momentum evaluation contract

Define an evaluator that consumes reconciled evidence and returns recommendations only. Each recommendation must include:

- recommendation ID and evaluation cycle ID;
- initiative, campaign, package, or operational subject;
- current authoritative state;
- proposed next transition;
- authority source;
- readiness evidence;
- dependency evidence;
- staffing and capacity evidence;
- validation and operational-health evidence;
- policy rules applied;
- blocked rules and rejected alternatives;
- priority and value basis;
- confidence and uncertainty classification;
- expected next state;
- required invoking office or canonical mechanism;
- escalation condition;
- expiration and reevaluation trigger.

The model must distinguish `recommend`, `continue`, `hold`, `pause`, `retry`, `request_staffing`, `request_validation`, `request_routing`, `escalate`, and `no_authorized_transition` outcomes.

### 2. Deterministic ranking and tie handling

Specify a bounded, explainable ranking model that considers only accepted policy and authoritative evidence. Cover at minimum:

- protected priority and explicit Steward direction;
- critical-path position;
- readiness and dependency clearance;
- blocker age and recoverability;
- staffing and compute capacity;
- validation status;
- operational risk;
- work-in-progress limits;
- starvation prevention;
- deadline or service-level commitments;
- expected value and bounded cost;
- fairness among equally authorized initiatives.

Ties, missing evidence, contradictory evidence, stale evidence, and unknown authority must fail closed or produce a named escalation; they must not be resolved by hidden intuition.

### 3. Explainability contract

Define machine-readable and Office-readable explanations that answer:

- What changed?
- Why is reevaluation occurring?
- What transition is recommended?
- Why is that transition authorized?
- Why is it ready?
- Why is it higher value than alternatives?
- Which alternatives were rejected and why?
- Which office or mechanism must act?
- What evidence would change the recommendation?
- When will it be reevaluated?

Every explanation must link to canonical evidence rather than copying unverifiable summaries.

### 4. Operational metrics

Define metrics and calculation sources for:

- campaign throughput;
- package cycle time;
- transition latency;
- blocker age and mean time to recovery;
- validation latency;
- readiness latency;
- staffing request latency;
- worker and provider utilization;
- idle authorized capacity;
- critical-path delay;
- stalled-campaign count;
- escalation frequency;
- false or withdrawn recommendation count;
- recommendation-to-action latency;
- reconciliation drift;
- unaccounted-state count;
- Steward interruption rate;
- proportion of transitions completed without Steward intervention.

Metrics must not become authority. They are evidence for operations and review.

### 5. Operational surfaces

Specify views for:

- Grace operations dashboard;
- Steward executive status;
- campaign momentum detail;
- blocker and escalation queue views using existing mechanisms;
- recommendation inspection;
- evidence drill-down;
- historical evaluation and policy audit;
- health and drift alerts.

Do not create a new Office. Extend existing Office and Steward surfaces through stable adapters.

### 6. Reconciliation and auditability

Define retention, replay, idempotency, and audit requirements for evaluation cycles and recommendations. The system must be able to reconstruct why a recommendation was made from durable evidence and the policy revision in force at that time.

## Deliverables

Create:

1. `docs/architecture/eoc_cme_momentum_evaluation_policy.md`
2. `docs/architecture/eoc_cme_recommendation_and_explanation_contract.md`
3. `docs/architecture/eoc_cme_operational_metrics_and_observability_model.md`
4. `docs/architecture/eoc_cme_operational_surface_specification.md`
5. `collaboration/work_packages/completions/WP-0667_completion_receipt.md`

## Non-Goals

- no runtime evaluator implementation;
- no autonomous approval;
- no machine-learning priority model;
- no opaque scoring;
- no duplicate KPI registry;
- no duplicate dashboard platform;
- no direct dispatch or scheduling.

## Validation

- every ranking factor maps to accepted policy or authoritative evidence;
- every recommendation names its authority source and invoking mechanism;
- missing or contradictory authority fails closed;
- metrics have defined formulas and source records;
- recommendation history is reconstructable;
- proposed surfaces reuse existing Office and Steward seams;
- the design cannot silently convert a recommendation into an action.

## Acceptance Criteria

The completed specification must let Grace inspect the highest-value authorized next transition, understand exactly why it was recommended, see why alternatives were rejected, and invoke only existing Estate mechanisms. The Steward must be able to audit momentum without becoming the continuous scheduler.

## Delivery

Open a pull request for Chief Architect review. Do not merge. Do not implement runtime behavior.
