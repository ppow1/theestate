# WP-0537 — Engineering Workforce Role Catalog and Staffing Plan Runtime

Status: Pending  
Execution Mode: PARALLEL-STAGED  
Owner: Office of Chief Architect / Human Resources Integration  
Execution Target: Codex  
Classification: Estate Internal  
Priority: Critical

## Depends On

- WP-0536 — Engineering Project Intake and Mobilization Runtime
- Helen Hiring and Onboarding Workflow

## Objective

Implement a production-grade engineering workforce role catalog and staffing-plan runtime so Helen can convert an authorized project demand into explicit, reusable worker roles and a source-lined staffing recommendation without inventing authority or treating generic models as interchangeable employees.

## Required Work

1. Define versioned engineering role profiles for technical lead, software engineer, computer-vision engineer, ML/data engineer, test/validation engineer, DevOps/runtime engineer, repository integrator, and specialist roles.
2. Each profile must include competencies, authority, prohibited actions, reporting line, security/access needs, provider/runtime compatibility, hardware needs, validation requirements, workload limits, continuity requirements, and onboarding corpus.
3. Generate staffing plans from WP-0536 project discovery: workstreams, role counts, sequencing, dependencies, concurrency, estimated capacity demand, required local/cloud mix, and acceptance checkpoints.
4. Distinguish role, seat, worker identity, model/provider implementation, and project assignment.
5. Support temporary project workers, standing department workers, specialist consultants, backups, and replacements.
6. Integrate with Helen's existing workflow for authority verification, candidate review, Ingrid review, onboarding, readiness, and checkpoints.
7. Produce human and machine-readable staffing briefs with evidence labels and explicit unresolved gaps.
8. Add CLI operations for role-list, role-show, plan-generate, plan-validate, plan-diff, and readiness-report.

## Production Requirements

- Versioned schemas and migrations.
- Deterministic staffing-plan IDs and idempotent regeneration.
- No automatic appointment or activation.
- Capacity-aware recommendations using WP-0532 through WP-0535 evidence.
- Audit history for role and plan changes.
- Conflict detection for concurrent updates.
- Windows-local operation and complete structured errors.

## Acceptance Tests

1. The pool-table computer-vision fixture yields a staffing plan containing appropriate vision, software, validation, and runtime competencies.
2. Missing role authority, access classification, provider compatibility, or validation standard blocks readiness.
3. Helen can consume the plan without reconstructing requirements manually.
4. A worker implementation can change providers without changing the canonical role or seat.
5. Re-running unchanged discovery produces the same plan rather than duplicate seats.
6. Capacity shortage produces a visible staffing constraint, not silent overcommitment.
7. Unit, integration, migration, concurrency, and end-to-end tests pass.

## Deliverables

- role catalog schemas and canonical profiles;
- staffing-plan generator and validator;
- Helen workflow adapter;
- capacity/provider evidence adapter;
- CLI, reports, fixtures, tests, documentation, validation recipe, and completion receipt.

## Constraints

- Do not create offices or appointment authority.
- Do not merge worker identity with model/provider identity.
- Do not bypass Helen, Ingrid, Steward-reserved appointments, or existing personnel registries.
- Do not return a decorative staffing list without executable onboarding requirements.

## Completion Standard

WP-0537 is complete only when an authorized engineering project can produce a validated, capacity-aware staffing plan that Helen can execute directly and that remains durable across provider, worker, and project changes.