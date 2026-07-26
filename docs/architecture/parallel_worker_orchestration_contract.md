# Parallel Worker Orchestration Contract

## Purpose

WP-4215 defines a provider-neutral, isolated planning boundary for safe concurrent engineering work. Its future staged implementation will evaluate immutable snapshots and emit advisory plans and findings. It will not execute a schedule, dispatch a worker, operate Git, or merge code.

## Safety invariants

1. **Exclusive ownership by default.** Every assignment names its file and branch boundary. Overlap is invalid unless a time-bounded authorization identifies the affected paths, assignments, authority, reason, and coordination protocol.
2. **Prerequisites before priority.** A high-priority package is ineligible until mandatory dependency and review gates have evidence. An override remains visible and cannot silently falsify readiness.
3. **Evidence before state.** Worker reports, telemetry, repository state, validation, review, and completion receipts are distinct evidence classes. Provider success alone is not verified completion.
4. **Plans are not actions.** Queue order, reassignment, merge order, and remediation are advisory outputs. No staged interface can enqueue, launch, mutate, approve, or merge.
5. **Unknown fails closed.** Missing capability, stale telemetry, ambiguous path normalization, incompatible adapter versions, or irreconcilable repository evidence blocks unsafe assignment rather than being guessed.
6. **History is append-only.** Lifecycle transitions, corrections, findings, overrides, and provenance remain replayable; materialized snapshots are reproducible from their cited inputs and policy versions.

## Information flow

The planner consumes governed campaign/work-package snapshots, offline repository/hosting snapshots, worker registrations, PL-0014 telemetry envelopes when available, and WP-4214 estimate results when available. Pure policy evaluators validate graph readiness, ownership, capability/health, lane capacity, priority, conflicts, completion evidence, and reconciliation. Outputs are versioned advisory queue/assignment/reassignment/merge-order plans, findings, verification results, metrics, and audit events.

PL-0014 and WP-4214 are optional contract providers. Absence is represented as unknown evidence, so neither implementation is a prerequisite for building or testing WP-4215. Adapter ports prevent imports from their private or future runtime modules.

## Ownership and integration boundary

The future implementation owns only `collaboration/workstreams/WP-4215/`. Repository campaign definitions, work-package records, live queues, workers, provider runtimes, Git refs, PRs, and completion records remain owned by their existing authorities. An `INSTALL_HANDOFF.md` may propose integrations but cannot perform them. Any production installation requires a new work package with named seams, owners, migrations, security review, validation, rollback, and acceptance authority.

## Decision precedence

Safety and authority constraints precede prerequisite readiness; readiness precedes capability and health; those precede priority and estimated duration. Within the eligible set, the versioned policy may consider critical path, declared priority, aging, lane/review capacity, ownership risk, and estimate ranges. Stable identifiers provide deterministic tie-breaking. No throughput or individual performance signal may override authorization, exclusivity, or completion evidence.

## Completion truth

An assignment may be provider-successful while its package remains unverified. Verification evaluates each package acceptance criterion against the exact repository snapshot, tests, validation, review state, receipt, dependency graph version, and unresolved findings. Only the appropriate external authority may accept or merge the result; the staged planner can report evidence but cannot confer institutional completion.
