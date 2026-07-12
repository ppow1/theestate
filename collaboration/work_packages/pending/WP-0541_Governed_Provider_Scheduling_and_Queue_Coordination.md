# WP-0541 — Governed Provider Scheduling and Queue Coordination

Status: Pending  
Execution Mode: SERIES  
Owner: Office of Chief Architect / Engineering Operations  
Execution Target: Codex  
Classification: Estate Internal  
Priority: Critical

## Depends On

- WP-0532 — Engineering Capacity Runtime and Dashboard
- WP-0533 — Engineering Provider Routing Runtime
- WP-0534 — Codex CLI Capability Discovery, Provider Registry, and Polling Policy
- WP-0535 — Engineering Provider Health and Telemetry Runtime
- WP-0540 — Engineering Assignment and Workstream Planning Runtime

## Objective

Implement production-grade governed provider scheduling and queue coordination that converts approved assignments and recommendation-only routing evidence into ordered, capacity-aware execution opportunities without creating a second Dispatch, provider registry, or authority system.

## Required Work

1. Define queue-item, scheduling-decision, reservation, deferment, retry, and release contracts linked to assignments, providers, execution sessions, workspaces, validation recipes, and governing authority.
2. Consume existing capability, capacity, health, routing, cost, and policy evidence; do not recompute or duplicate those domains.
3. Implement deterministic eligibility, priority, fairness, capacity reservation, affinity, anti-affinity, starvation prevention, maintenance windows, quota protection, and backpressure rules.
4. Keep provider routing recommendation-only; scheduling may prepare or reserve work but may not bypass Dispatch or required Steward/Traffic Controller authorization.
5. Support local-first policy, cloud escalation, manual pinning, provider exclusion, emergency pause, and bounded retry with explicit rationale.
6. Coordinate queue depth, active jobs, workspace leases, worker availability, provider concurrency, GPU/VRAM constraints, and dependency readiness.
7. Preserve append-only decision history, evidence snapshots, policy version, actor, timestamps, overrides, failures, and supersession.
8. Expose CLI and machine-readable operations for enqueue, inspect, recommend, reserve, release, defer, pause, resume, explain, and report.
9. Recover safely after process restart, expired reservations, provider failure, quota exhaustion, or stale evidence.
10. Produce Office-consumable queue and scheduling reports without making the Office the scheduler.

## Production Requirements

- Atomic queue mutations and reservation leases.
- Idempotent enqueue and release operations.
- Deterministic ordering under equal inputs.
- Concurrency-safe multi-worker access.
- Schema migrations and backward compatibility.
- Complete explainability for every scheduling outcome.
- No silent cloud use or quota-consuming probes.
- Windows-local operation and restart recovery.

## Acceptance Tests

1. Ready assignments are ordered using current capability, capacity, health, cost, policy, and dependency evidence.
2. Unhealthy, stale, saturated, unauthorized, or incompatible providers are excluded with explicit reasons.
3. Local providers are preferred where policy and evidence permit; cloud escalation requires recorded justification.
4. Parallel schedulers cannot double-reserve one assignment or overbook provider capacity.
5. Expired reservations and crashed schedulers recover without losing assignments or duplicating execution.
6. Manual pause, provider exclusion, and governed override are auditable and reversible.
7. Existing Dispatch remains the only execution release path.
8. Unit, integration, concurrency, failure-injection, recovery, policy, and Windows end-to-end tests pass.

## Deliverables

- queue, reservation, and scheduling schemas;
- scheduling and recovery runtime;
- existing-provider-evidence adapters;
- CLI and Office reports;
- tests, documentation, validation recipe, and completion receipt.

## Constraints

- Do not create a second Dispatch, provider registry, routing engine, execution-session runtime, or authority model.
- Do not auto-dispatch merely because a provider is recommended or reserved.
- Do not collapse capability, capacity, health, cost, and authority into one score without preserving source evidence.

## Completion Standard

WP-0541 is complete only when approved assignments can be queued, explained, capacity-reserved, deferred, recovered, and presented for existing governed Dispatch using current provider evidence without duplicate execution, hidden cloud consumption, or competing authority paths.