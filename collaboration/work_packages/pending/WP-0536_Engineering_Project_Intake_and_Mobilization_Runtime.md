# WP-0536 — Engineering Project Intake and Mobilization Runtime

Status: Pending  
Execution Mode: SERIES  
Owner: Office of Chief Architect / Engineering Operations  
Execution Target: Codex  
Classification: Estate Internal  
Priority: Critical

## Objective

Implement a production-grade Engineering Project Intake and Mobilization Runtime that converts a Steward-authorized product or repository request into a governed, source-lined engineering project record suitable for staffing, provisioning, dispatch, validation, and operational reporting.

This is not an MVP intake form. It is the canonical start of an engineering engagement.

## Required Work

1. Define canonical schemas for project request, business objective, technical objective, repository targets, deliverables, constraints, urgency, data classification, hardware needs, provider constraints, validation expectations, acceptance authority, risks, dependencies, and project state.
2. Support intake from the Steward, Grace/Operations, authorized offices, and imported external-repository briefs while preserving the requesting authority and source evidence.
3. Add deterministic project lifecycle states: REQUESTED, CLARIFICATION_REQUIRED, AUTHORITY_VERIFIED, SECURITY_REVIEW, TECHNICAL_DISCOVERY, STAFFING_PLAN, PROVISIONING, READY_FOR_EXECUTION, ACTIVE, BLOCKED, VALIDATING, ACCEPTANCE_PENDING, COMPLETE, SUSPENDED, and CANCELLED.
4. Verify repository identity, default branch, access mode, local checkout location, license/provenance notes, secret-handling requirements, test commands, build commands, runtime requirements, and protected data before execution begins.
5. Produce a technical discovery record that identifies workstreams, unknowns, required competencies, likely provider classes, local hardware requirements, and measurable success criteria.
6. Generate a mobilization readiness report consumed by Helen, Grace, Engineering, Ingrid, Traffic Controller, Dispatch, Validation, and the Office without making intake a new authority system.
7. Preserve append-only project history, supersession, decision rationale, timestamps, actors, and evidence references.
8. Expose CLI and machine-readable interfaces for create, inspect, update-state, validate-readiness, list-blockers, and produce-report.
9. Integrate with existing work-package, dispatch, execution-session, provider evidence, validation, mailbox, and Office systems through adapters rather than duplication.
10. Include migration and backfill support for existing repositories and projects.

## Production Requirements

- Idempotent writes and deterministic identifiers.
- Schema versioning and forward-compatible migrations.
- Atomic state transitions with explicit authorization checks.
- No secrets stored in project records.
- Crash-safe persistence and recovery.
- Concurrent-reader safety and conflict detection for updates.
- Complete audit trail for every transition.
- Structured errors suitable for Office surfaces and automation.
- Windows-local operation under `A:\theestate` and configurable external repository roots.

## Acceptance Tests

1. A Steward request for an external computer-vision repository produces a complete project record with repository, hardware, staffing, security, validation, and acceptance fields.
2. Missing authority, repository access, validation criteria, or classification blocks mobilization with explicit reasons.
3. Repeated intake is idempotent and does not create duplicate projects.
4. State transitions reject unauthorized or invalid movement.
5. Existing dispatch, validation, and provider systems are referenced rather than recreated.
6. Project history remains reconstructable after updates and restarts.
7. A generated readiness report clearly distinguishes verified evidence, Steward-reported facts, assumptions, and unresolved unknowns.
8. Focused, integration, recovery, and end-to-end tests pass on Windows.

## Deliverables

- intake and project schemas;
- project registry/runtime and migrations;
- CLI and reports;
- adapters to existing Estate systems;
- fixtures for an external pool-table ball-detection project;
- unit, integration, concurrency, recovery, and end-to-end tests;
- documentation, validation recipe, and completion receipt.

## Constraints

- Do not create a second work-package registry, provider registry, scheduler, dispatch system, validation authority, or Office control plane.
- Do not treat project intake as authorization to execute.
- Do not store credentials, tokens, or private repository secrets.
- Do not promote technical discovery into institutional acceptance.

## Completion Standard

WP-0536 is complete only when a real external engineering project can enter the Estate once, retain complete lineage and governance, survive restart and concurrent access, and produce an actionable mobilization record that downstream staffing and execution systems can consume without manual reconstruction.