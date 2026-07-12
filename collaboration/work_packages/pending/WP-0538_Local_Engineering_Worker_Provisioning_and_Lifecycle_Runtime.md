# WP-0538 — Local Engineering Worker Provisioning and Lifecycle Runtime

Status: Pending  
Execution Mode: PARALLEL-STAGED  
Owner: Office of Chief Architect / Engineering Operations  
Execution Target: Codex  
Classification: Estate Internal  
Priority: Critical

## Depends On

- WP-0537 — Engineering Workforce Role Catalog and Staffing Plan Runtime
- Existing resident/worker identity, mailbox, provider, dispatch, and execution-session systems

## Objective

Implement production-grade provisioning and lifecycle management for local engineering workers so approved staffing plans can become isolated, recoverable, auditable working environments on Estate hardware.

## Required Work

1. Define worker-instance and assignment schemas that bind canonical worker/seat identity to role, project, provider implementation, local runtime, repository workspace, mailbox, security profile, resource limits, and lifecycle state.
2. Support lifecycle states REQUESTED, APPROVED, PROVISIONING, READY, ACTIVE, PAUSED, DRAINING, FAILED, RECOVERING, RETIRED, and REVOKED.
3. Provision isolated local workspaces, Python/runtime environments, toolchains, model bindings, cache/temp locations, logging, and repository-scoped configuration using configurable A-drive roots.
4. Validate GPU/CPU/RAM/disk requirements against capacity and health evidence before activation.
5. Integrate with existing provider registry, routing recommendations, dispatch, execution leases, cancellation, recovery, and execution sessions.
6. Provide heartbeat, workload, error, restart, checkpoint, and teardown evidence without submitting work outside governed dispatch.
7. Support reproducible rebuild, backup/restore, clean retirement, credential revocation, and orphan detection.
8. Expose CLI and machine APIs for provision, inspect, activate, pause, drain, recover, retire, list, and readiness-report.

## Production Requirements

- Idempotent provisioning and rollback on partial failure.
- Least-privilege repository and filesystem access.
- No secrets in manifests or logs.
- Resource quotas and collision-safe workspace allocation.
- Crash recovery and stale-lock handling.
- Structured logs, metrics, and append-only lifecycle history.
- Windows path, process, and service handling tested on the target host.

## Acceptance Tests

1. An approved local computer-vision worker can be provisioned with a dedicated workspace, runtime, tools, provider binding, and repository assignment.
2. Insufficient VRAM, disk, runtime, authorization, or repository access blocks activation with explicit evidence.
3. Interrupted provisioning rolls back or resumes safely.
4. Repeated provisioning requests do not duplicate workers or workspaces.
5. Pause, drain, recovery, retirement, and revocation preserve audit history and prevent unauthorized execution.
6. Existing dispatch and execution-session paths are reused.
7. Unit, integration, recovery, security, resource-contention, and end-to-end tests pass.

## Deliverables

- worker provisioning and lifecycle runtime;
- environment/workspace builders and rollback;
- provider, capacity, dispatch, mailbox, and identity adapters;
- CLI, reports, diagnostics, fixtures, tests, documentation, validation recipe, and completion receipt.

## Constraints

- Do not create a second provider control plane, scheduler, personnel registry, identity system, or dispatch path.
- Do not activate workers before Helen/readiness and required authority gates are satisfied.
- Do not grant broad host or repository access by default.

## Completion Standard

WP-0538 is complete only when approved local engineering workers can be provisioned, activated, observed, recovered, and retired reproducibly on Estate hardware without manual environment reconstruction or boundary bypass.