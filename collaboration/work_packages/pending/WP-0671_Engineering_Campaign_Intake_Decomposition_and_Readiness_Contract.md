# WP-0671 — Engineering Campaign Intake, Decomposition, and Readiness Contract

Status: Pending
Owner: Chief Architect
Execution lane: Codex
Campaign: CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION
Depends on: WP-0670

## Objective

Define the governed path by which approved engineering intent becomes an executable campaign and a dependency-safe set of work packages.

## Required Work

1. Define intake inputs for ideas, discoveries, accepted proposals, architectural decisions, defects, operational blockers, and Steward directives.
2. Define when an item remains in discovery, becomes a planning package, becomes an engineering campaign, or is rejected/held.
3. Define campaign identity, parent authority, owner, priority, scope, non-goals, milestones, dependency graph, risk class, acceptance lane, and completion evidence.
4. Define work-package decomposition rules for atomicity, shared-file collision control, branch ownership, integration checkpoints, validation recipes, completion receipts, and rollback.
5. Define readiness gates for architecture, staffing, dependencies, provider capability, test environment, data/privacy, budget, and protected approvals.
6. Define campaign amendment, pause, cancellation, supersession, and replan procedures.
7. Reuse PTM and current work-package validation conventions; do not introduce a parallel planning registry.

## Deliverables

- `docs/architecture/engineering_campaign_intake_contract.md`
- `docs/architecture/engineering_campaign_decomposition_standard.md`
- `docs/architecture/engineering_campaign_readiness_gate_model.md`
- `docs/templates/engineering_campaign_charter_template.md`
- `docs/templates/engineering_work_package_template.md`
- `collaboration/work_packages/completions/WP-0671_completion_receipt.md`

## Validation

- Every readiness gate names evidence and authority.
- Every package belongs to one primary campaign.
- Dependencies are machine-checkable or explicitly marked manual.
- Shared-file collision controls are defined.
- No campaign may reach execution without accepted architecture and readiness evidence.

## Acceptance Criteria

A fresh Chief Architect must be able to convert approved intent into a complete campaign package that Codex can execute without deriving missing scope, order, authority, or acceptance requirements.

## Delivery

Open a PR for Chief Architect review. Do not merge. Do not implement campaign runtime behavior.
