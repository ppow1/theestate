# WP-0540 — Engineering Assignment and Workstream Planning Runtime

Status: Pending  
Execution Mode: SERIES  
Owner: Office of Chief Architect / Engineering Operations  
Execution Target: Codex  
Classification: Estate Internal  
Priority: Critical

## Depends On

- WP-0536 — Engineering Project Intake and Mobilization Runtime
- WP-0537 — Engineering Workforce Role Catalog and Staffing Plan Runtime
- WP-0539 — External Repository Access and Workspace Runtime

## Objective

Implement a production-grade assignment-planning runtime that converts an approved engineering project into explicit workstreams, bounded assignments, dependencies, completion evidence, and worker handoffs suitable for existing Dispatch and execution-session systems.

## Required Work

1. Define canonical workstream and assignment schemas containing project, objective, scope, excluded scope, repository and workspace references, required competency, provider constraints, dependencies, priority, risk, acceptance tests, validation recipe, evidence outputs, owner, and status.
2. Support SERIES, PARALLEL-INDEPENDENT, and PARALLEL-STAGED plans with explicit merge and INSTALL-HANDOFF points.
3. Detect shared hot files, incompatible branch plans, circular dependencies, unbounded scope, missing validation, and duplicate assignments before dispatch.
4. Produce deterministic assignment identifiers and idempotent regeneration when project evidence has not changed.
5. Integrate staffing-plan workers, workspace leases, provider recommendations, work packages, Dispatch, execution sessions, cancellation, recovery, and validation through existing adapters.
6. Require every assignment to identify completion evidence, expected changed paths, test commands, artifact locations, and escalation conditions.
7. Preserve planning revisions, supersession, rationale, source evidence, and impact analysis.
8. Expose CLI and machine-readable operations for plan, inspect, validate, revise, approve-for-dispatch, list-ready, list-blocked, and report.
9. Generate human-readable assignment briefs and exact worker handoff payloads without directly dispatching work.
10. Include backpressure rules so assignments are not released when workers, providers, capacity, health, repository access, or validation prerequisites are unavailable.

## Production Requirements

- Deterministic dependency graph and cycle detection.
- Atomic plan revisions and conflict detection.
- No implicit expansion of worker or provider authority.
- Stable schema versioning and migration support.
- Complete audit history and source lineage.
- Windows path compatibility and external-repository support.

## Acceptance Tests

1. A computer-vision project decomposes into discovery, data, detection, calibration, integration, and validation workstreams with explicit dependencies.
2. Parallel plans identify shared hot files and require staged installation where appropriate.
3. Missing tests, unclear completion evidence, duplicate scope, or cycles block approval.
4. Regenerating an unchanged plan produces the same identifiers without duplicate assignments.
5. Approved assignments are consumable by existing Dispatch and execution-session systems.
6. Cancelled or revised assignments preserve prior lineage and do not lose worker output.
7. Unit, integration, graph, concurrency, recovery, and Windows end-to-end tests pass.

## Deliverables

- workstream and assignment schemas;
- planning, dependency, conflict, and revision runtimes;
- assignment briefs and handoff payloads;
- adapters to existing staffing, workspace, Dispatch, execution, and validation systems;
- tests, documentation, validation recipe, and completion receipt.

## Constraints

- Do not create a second Dispatch, scheduler, queue, work-package registry, or acceptance authority.
- Do not dispatch merely because a plan exists.
- Do not allow vague assignments such as “finish the project.”

## Completion Standard

WP-0540 is complete only when an approved project can be transformed into bounded, dependency-correct, evidence-bearing assignments that are safe to parallelize, ready for existing governed dispatch, and fully auditable from project objective through worker handoff.