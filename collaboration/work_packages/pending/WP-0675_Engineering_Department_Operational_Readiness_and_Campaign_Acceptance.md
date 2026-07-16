# WP-0675 — Engineering Department Operational Readiness and Campaign Acceptance

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Campaign: CAMPAIGN-0670 Engineering Department Operationalization  
Depends on: WP-0670, WP-0671, WP-0672, WP-0673, WP-0674

## Objective

Integrate and validate all CAMPAIGN-0670 outputs, prove that the Engineering Department can execute one governed engineering campaign from approved intake through acceptance preparation, and produce the final operational-readiness and campaign-acceptance package.

This package is the campaign closure gate. It must not merely summarize earlier documents. It must test the integrated operating model against real repository mechanisms and produce evidence showing whether the department is ready, conditionally ready, or not ready.

## Required Inputs

Review and reconcile:

- `collaboration/campaigns/CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION.md`
- all deliverables and completion receipts from WP-0670 through WP-0674
- the Engineering Department Charter and operating guide
- PTM campaign, package, dependency, readiness, scheduling, and acceptance contracts
- dispatch and execution-provider contracts
- validation and operational-readiness closure systems
- mailbox, message, board, parking-lot, and escalation systems
- Engineering Notebook, metrics, reporting, and reflection/continuity standards
- current Codex and local-AI execution seams
- existing Chief Architect and Steward acceptance conventions

## Required Work

### 1. Integrated architecture reconciliation

Produce a reconciliation matrix mapping each CAMPAIGN-0670 requirement to:

- the authoritative specification;
- the existing mechanism reused;
- any new adapter or contract proposed;
- the responsible office;
- the validation evidence;
- unresolved gaps or contradictions.

Resolve or explicitly escalate contradictions among package outputs. Do not silently choose one contract over another.

### 2. End-to-end pilot campaign

Select or construct one bounded, non-production-destructive engineering pilot that exercises the complete lifecycle:

```text
approved campaign intake
  -> decomposition
  -> readiness evaluation
  -> staffing/capability check
  -> execution-lane selection
  -> dispatch or Codex handoff
  -> branch and PR production
  -> evidence collection
  -> package validation
  -> integration checkpoint
  -> campaign validation
  -> operational-readiness review
  -> Chief Architect acceptance preparation
  -> Steward-facing final package
```

The pilot may use a dry-run or fixture where actual implementation would create unacceptable risk, but every mocked boundary must be named and justified.

### 3. Authority-boundary proof

Demonstrate that:

- the Engineering Department does not set institutional priority;
- Grace coordinates momentum but does not approve architecture;
- Helen supplies staffing but does not approve engineering truth;
- Alfred routes communications but does not execute packages;
- Codex and local AI are providers, not offices;
- workers cannot self-approve;
- Chief Architect retains engineering acceptance;
- Steward retains protected and final institutional authority;
- no second scheduler, dispatch queue, validation path, registry, or acceptance system exists.

### 4. Failure-mode exercises

Exercise and document at minimum:

- intake with missing authority;
- package with unmet dependency;
- unavailable worker or provider;
- provider failure after partial work;
- validation failure;
- missing validation recipe;
- stale branch or conflicting PR;
- contradictory completion evidence;
- context rollover during execution;
- authority blocker requiring Steward action;
- post-merge regression;
- campaign pause and resume.

Each case must produce an explicit state, owner, evidence path, recovery path, and escalation outcome.

### 5. Operational-readiness assessment

Score and justify readiness across:

- governance and authority clarity;
- intake and decomposition;
- dependency and readiness truth;
- staffing and capability supply;
- provider and execution-lane routing;
- branch and integration discipline;
- evidence completeness;
- validation reliability;
- acceptance clarity;
- communication routing;
- metrics and observability;
- Notebook and architectural memory;
- reflection and continuity;
- recovery and escalation;
- Steward workload reduction.

Use `Ready`, `Conditionally Ready`, or `Not Ready` with evidence. No aggregate score may hide a failed protected gate.

### 6. Final campaign acceptance package

Create a Steward- and Chief-Architect-readable package containing:

- campaign objective and authority basis;
- included work packages and completion status;
- deliverable inventory;
- integration and validation evidence;
- pilot results;
- authority-boundary proof;
- unresolved conditions;
- operational risks;
- recommended acceptance decision;
- implementation or rollout prerequisites;
- exact next campaign recommendation;
- archive and continuity instructions.

### 7. Campaign closure records

Update campaign status and produce machine-readable and human-readable closure records without marking the campaign accepted until the protected acceptance action occurs.

## Deliverables

Create or update:

1. `docs/operations/Engineering_Department_Operational_Readiness_Assessment_v1.md`
2. `operations/departments/engineering/CAMPAIGN_0670_end_to_end_pilot_report.md`
3. `operations/departments/engineering/CAMPAIGN_0670_authority_boundary_proof.md`
4. `operations/departments/engineering/CAMPAIGN_0670_failure_mode_validation_report.md`
5. `collaboration/campaigns/CAMPAIGN_0670_ACCEPTANCE_PACKAGE.md`
6. machine-readable campaign closure/readiness record in the canonical runtime location
7. campaign status update that remains pending acceptance until authorized
8. `collaboration/work_packages/completions/WP-0675_completion_receipt.md`

## Non-Goals

- no broad production rollout;
- no automatic campaign acceptance;
- no change to constitutional authority;
- no replacement of PTM, dispatch, validation, readiness, mailbox, or registry systems;
- no unrelated product implementation;
- no claim of readiness without completed evidence.

## Required Validation

Before claiming completion, verify programmatically and manually that:

- all six CAMPAIGN-0670 Pending packages exist and are complete;
- all required package completion receipts exist;
- every campaign requirement maps to a deliverable and evidence source;
- the pilot traverses every required lifecycle stage or records a justified fixture boundary;
- all failure cases produce explicit fail-closed outcomes;
- authority boundaries are demonstrably preserved;
- no duplicate scheduler, queue, registry, validator, or acceptance path was introduced;
- campaign status is not marked accepted without Chief Architect and Steward action;
- the final acceptance package is sufficient for a fresh reviewer without chat context.

Include exact validation commands and results in the completion receipt.

## Acceptance Criteria

CAMPAIGN-0670 is ready for protected acceptance when the Engineering Department has demonstrated one coherent, evidence-driven, recoverable, and constitutionally bounded operating model capable of moving an approved engineering campaign from intake to final acceptance preparation without requiring the Steward to serve as the continuous scheduler.

## Delivery

Open a pull request for Chief Architect review. Do not merge. Do not mark the campaign accepted. Present the completed campaign acceptance package for protected review.