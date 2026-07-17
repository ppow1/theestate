# WP-0690 — Authority-Aware Operational Action Taxonomy

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Campaign: CAMPAIGN-0681 — Estate Operationalization  
Primary campaign ID: CAMPAIGN-0681  
Depends on: WP-0688, WP-0689  
Integration gate: G1 — Canonical and authority freeze

## Objective

Define and implement the canonical operational action taxonomy that distinguishes observation, recommendation, coordination, execution request, authorized mechanical action, office decision, protected institutional decision, and acceptance.

This package must make authority visible and machine-checkable without transferring authority or creating a parallel governance system.

## Constitutional Precedence

Accepted Estate constitutional, office, communication, campaign, Engineering, PTM, Dispatch, readiness, validation, evidence, and acceptance standards remain authoritative.

If this package conflicts with an accepted canonical artifact, the accepted artifact prevails. Any required authority change must be isolated as a protected architectural decision and may not be implemented silently under this package.

## Required Inputs

Read completely before implementation:

- `AI_HINTS.md`
- `AI_START_HERE.md`
- `AI_COMMUNICATION_HINTS.md`
- `collaboration/campaigns/CAMPAIGN_0681_ESTATE_OPERATIONALIZATION.md`
- `collaboration/work_packages/planning/CAMPAIGN_0681_manifest.json`
- WP-0688 and WP-0689 plus their completion evidence when available
- canonical office charters and authority records for the Steward, Chief Architect, Grace, Helen, and Alfred
- CAMPAIGN-0670 authority, readiness, validation, evidence, integration, and acceptance artifacts
- canonical PTM, Dispatch, mailbox, repository-message, merge, deployment, and acceptance mechanisms

Moved paths must be resolved through repository evidence. Do not invent replacements.

## Required Work

### 1. Canonical action classes

Define at minimum:

1. `observe` — read canonical state without changing it;
2. `recommend` — produce an evidence-backed proposed next action;
3. `coordinate` — organize or route already-authorized work within an office's existing authority;
4. `request_execution` — submit governed executable work through an accepted mechanism;
5. `mechanical_action` — perform a bounded action explicitly delegated by canonical policy;
6. `office_decision` — decision reserved to a named office or officeholder;
7. `protected_decision` — decision requiring Steward or another explicitly protected authority;
8. `acceptance` — formal acceptance in an existing acceptance lane.

Define any additional subclasses only where existing Estate artifacts require them.

### 2. Action descriptor contract

Create a minimal machine-readable descriptor for operational actions. Reuse existing identities and references rather than creating a second registry.

Each descriptor must include at minimum:

- action ID and action class;
- proposed actor and institutional role;
- source event or state references;
- target object or mechanism;
- required authority and authority evidence;
- readiness prerequisites;
- validation and evidence requirements;
- side-effect classification;
- protected surfaces touched;
- idempotency and retry policy;
- stop or escalation conditions;
- disposition state;
- decision or execution evidence after disposition.

### 3. Authority evaluation

Implement a deterministic evaluation surface that can answer:

- Is this action observational, advisory, coordinative, mechanical, decisional, protected, or acceptance-related?
- Is the proposed actor authorized?
- Which prerequisites or approvals are missing?
- Which canonical mechanism must carry the action?
- Must execution stop and escalate?
- What evidence must be produced?

Evaluation must fail closed when authority, identity, scope, or evidence is ambiguous.

### 4. Office boundary mapping

Map the action classes to existing authority boundaries, including at minimum:

- Grace may observe, recommend, and coordinate within her accepted operational authority but may not acquire architectural, staffing, engineering-acceptance, merge, deployment, or final institutional authority;
- Helen may provide staffing and capability decisions within her accepted lane but may not set engineering architecture, priority, or acceptance;
- Alfred may route communications and coordinate Chief-of-Staff functions but may not become the executor or acceptance authority merely by routing work;
- Chief Architect retains engineering architecture and engineering acceptance;
- Steward retains final and protected institutional authority;
- Codex and local models are execution providers, not offices or authorities.

Use canonical office records as the source of truth rather than relying on this summary alone.

### 5. Integration adapters

Provide the narrow interfaces needed by later CAMPAIGN-0681 packages to classify proposed actions before they reach PTM, Dispatch, mailbox, repository-message, validation, merge, deployment, or acceptance seams.

Do not implement the Continuous Momentum Engine or broad action adapters in this package.

### 6. Evidence and explanations

Every evaluation must be explainable through repository-grounded evidence. The output must identify:

- classification;
- allowed, denied, or requires-review disposition;
- authoritative basis;
- missing prerequisites;
- required mechanism;
- required decision owner;
- next safe action.

## Required Deliverables

1. canonical operational action taxonomy specification in the nearest existing architecture or operations seam;
2. machine-readable action descriptor schema or contract;
3. deterministic authority-evaluation implementation in the nearest existing canonical runtime seam;
4. office-boundary mapping derived from canonical authority records;
5. tests covering allowed, denied, ambiguous, and protected cases;
6. integration guidance for later CAMPAIGN-0681 packages;
7. `collaboration/work_packages/completions/WP-0690_completion_receipt.md`.

## Explicit Non-Goals

Do not:

- change office authority;
- create a new office, authority registry, scheduler, queue, dispatch system, or acceptance system;
- implement Grace, Helen, or Alfred operational surfaces;
- implement the Continuous Momentum Engine;
- perform automatic merge, deployment, protected decisions, or acceptance;
- infer authority from titles, filenames, or model identity;
- treat recommendation or mechanical execution as approval or acceptance.

## Required Validation

Before claiming completion, prove that:

- every action class is distinct and machine-checkable;
- ambiguous authority fails closed;
- unauthorized actors are denied;
- protected actions stop for the correct authority;
- recommendations cannot be mistaken for decisions;
- mechanical actions require explicit delegation;
- acceptance cannot be inferred from execution success;
- existing canonical mechanisms are referenced rather than duplicated;
- office-boundary tests cover Grace, Helen, Alfred, Chief Architect, Steward, and execution providers;
- repository and package-specific tests pass.

Record exact commands and results in the completion receipt.

## Acceptance Criteria

WP-0690 is complete when the Estate has one canonical, testable method for classifying operational actions and determining whether a proposed actor may observe, recommend, coordinate, request, mechanically execute, decide, escalate, or accept—without changing existing authority and without creating a parallel governance path.

## Delivery

Commit this package as one bounded CAMPAIGN-0681 work-package commit. Stop at G1 for Chief Architect review. Do not merge, deploy, mark the campaign launched, or infer acceptance.
## Executable Validation Commands

Run the following commands from the repository root after implementation and
after creating this package's completion receipt:

    pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0690
    git diff --check

Run all additional affected-subsystem tests discovered during implementation.
Record every exact command, result, environment, unresolved gap, and failure
disposition in the package completion receipt.

A prose expected outcome is not a substitute for executing the commands above.
