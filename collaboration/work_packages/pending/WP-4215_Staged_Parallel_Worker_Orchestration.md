# WP-4215 — Staged Parallel Worker Orchestration

- **Status:** Pending
- **Source:** `PL-0016 — Parallel Worker Orchestration`
- **Mode:** isolated staged implementation
- **Implementation root:** `collaboration/workstreams/WP-4215/`
- **Install authority:** none; a separate install-handoff work package is mandatory

## 1. Mission

Implement and validate a provider-neutral orchestration **model and decision-planning layer** for coordinating concurrent AI coding assignments safely. The staged implementation must register workers and capabilities, model campaigns and assignment lifecycles, enforce dependencies and exclusive ownership, identify conflicts and unhealthy or abandoned work, plan queues and engineering lanes, support authorized reassignment and overrides, verify completion evidence, and preserve an append-only audit trail.

This package does not implement or install a runtime scheduler, worker runtime, dispatcher, CLI executor, Git automation, merge automation, or production integration.

## 2. Mandatory implementation and authority boundary

All implementation, schemas, fixtures, tests, reports, and the implementation completion receipt MUST remain beneath `collaboration/workstreams/WP-4215/`. The implementer must not edit production or shared runtime, scheduling, dispatch, provider, queue, campaign, CLI, Git, merge, Alfred, Helen, Grace, Open WebUI, Local Compute, resident, registry, or worker files. Tests may write only beneath the staged root or per-test temporary directories.

The staged component accepts snapshots and emits advisory plans, diagnostics, and proposed transitions. It must never launch a worker, create or mutate a branch or PR, merge code, enqueue production work, approve completion, or modify a canonical repository record. A separately authorized install-handoff package must name every production seam, owner, migration, compatibility check, validation gate, rollback, and security review before staged output can affect live execution.

## 3. Provider-neutral worker registration

Define versioned records for `worker_registration`, `worker_capability`, and `worker_health_snapshot`. A registration must include:

- stable orchestrator worker ID and provider-scoped opaque ID;
- worker kind: `codex`, `chatgpt`, `local`, or `external` (extensible without changing lifecycle semantics);
- provider/adapter and execution-environment references;
- declared and verified capabilities, limitations, supported repository operations, concurrency limit, and availability window;
- authorization scope, allowed engineering lanes, trust/evidence level, registration status, freshness, and provenance;
- health assessment and PL-0014 telemetry correlation when available.

Capabilities are versioned descriptions, not claims of authorization or health. Unknown providers and future workers use extension fields behind a namespaced adapter contract; they must not be coerced into Codex semantics. Registration never starts a runtime, grants repository access, or assigns work.

## 4. Canonical staged records

Provide JSON Schema Draft 2020-12 contracts, examples, stable identifiers, UTC RFC 3339 timestamps, explicit versions, and forward-compatibility rules for:

1. worker registration, capability description, availability, and health snapshot;
2. campaign execution snapshot and engineering-lane definition;
3. work-package and dependency-graph snapshot;
4. assignment, attempt, ownership lease, and lifecycle transition;
5. queue snapshot, priority policy, and advisory scheduling decision;
6. conflict, prerequisite violation, staleness, abandonment, and merge-risk finding;
7. reassignment plan and operator override;
8. completion-verification and repository-reconciliation result;
9. throughput metric window and evidence-quality annotation;
10. append-only audit event and provenance envelope.

Every derived record cites source record IDs/hashes, observed-at/as-of time, policy and schema versions, actor or system identity, adapter version, decision reason, and supersession links. Missing, stale, conflicting, and unknown values remain explicit. Corrections append new events and never silently rewrite history.

## 5. Campaign, graph, lane, and queue model

A `campaign_execution_snapshot` references the governed campaign and package definitions; it must not become a competing task registry. It contains campaign state (`proposed`, `ready`, `active`, `held`, `blocked`, `verifying`, `complete`, `cancelled`, or `unknown`), package state projections, graph version, readiness evidence, lane membership, queue snapshot, active assignments, unresolved findings, and provenance.

The dependency graph is a directed acyclic graph of stable package IDs with prerequisite type, required completion/validation state, evidence references, and optional review/merge gates. Reject cycles, unknown nodes, self-dependencies, contradictory edges, and graph-version drift. Eligibility requires every mandatory prerequisite to satisfy its declared gate; a textual assertion or worker completion claim is insufficient.

Engineering lanes partition work by repository boundary, subsystem, campaign phase, risk class, or operator-defined isolation boundary. Each lane declares concurrency, allowed worker capabilities, branch policy, review gate, queue policy, and integration order. Queue entries preserve enqueue time, eligibility, priority inputs, dependency state, requested capabilities, ownership footprint, aging, hold reasons, and provenance. Lane and queue planning is advisory and deterministic for the same normalized snapshot and policy version.

## 6. Assignment lifecycle, file ownership, and branch ownership

The lifecycle is:

`proposed -> eligible -> reserved -> assigned -> acknowledged -> active -> review_ready -> verifying -> completed`

Permitted exceptional terminal or supervisory states are `declined`, `blocked`, `stalled`, `abandoned`, `superseded`, `cancelled`, `failed`, and `unknown`. Each transition requires a reason, evidence, actor/authority, timestamp, prior version, and idempotency key. Out-of-order or duplicate transitions are retained as findings but cannot regress materialized state. Reassignment closes or supersedes the prior attempt and creates a new linked attempt; it never reuses the old attempt ID.

Every assignment must declare an explicit ownership boundary before becoming `assigned`:

- exact files, directories, and/or normalized path patterns, including generated artifacts;
- excluded paths and shared read-only paths;
- branch name/ref, base ref and expected head when known;
- worktree/workspace reference when supplied;
- permitted operations and expiry/renewal policy;
- package, campaign, worker, attempt, and lane IDs;
- exceptional overlap authorization, authorizer, scope, reason, expiry, and required coordination protocol.

Ownership is exclusive by default. Two live assignments must never own overlapping files or ambiguous ancestor/descendant patterns unless an authorized, bounded overlap record exists. Read-only access is not ownership. A branch has at most one owning assignment/workstream unless explicit shared-branch authorization names all participants and integration rules. Expired leases do not silently free ownership: reconciliation must first classify residual branch/PR/worktree risk.

## 7. Conflict and risk detection

The planner must produce stable findings with severity, affected records, evidence, explanation, remediation, policy version, and disposition for:

- dependency or prerequisite violations;
- duplicate package/attempt assignments and idempotency collisions;
- exact, glob, case-normalization, rename, generated-file, and directory ownership overlap;
- stale assignments and telemetry freshness failure;
- abandoned work based on explicit policy and evidence, distinct from merely stalled or unknown work;
- branch-name, base/head drift, shared-branch, and incompatible branch ownership conflicts;
- multiple or conflicting PRs for one assignment/package, overlapping PR change sets, and superseded PRs;
- merge risk from overlapping diffs, dependency order, base drift, unresolved checks/reviews, schema/migration ordering, or integration sequence;
- worker unavailability, capability mismatch, unhealthy worker, concurrency excess, and lane-policy violations.

Detection consumes repository snapshots and provider evidence; it does not call Git/GitHub or mutate branches/PRs. Case sensitivity and path normalization follow the target repository policy and must fail closed when unknown. Findings are never presented as proven resolution until later reconciliation supplies evidence.

## 8. Worker health, stalls, abandonment, and reassignment

Use PL-0014's published normalized observations through an adapter boundary when available. Until implemented, synthetic fixtures and explicit `telemetry_unavailable`/`unknown` states must allow offline operation. Health combines freshness, provider status, observed lifecycle activity, capacity declaration, and evidence reliability without inferring personal traits.

Stall policy is versioned by worker/provider/lane class and compares last qualifying activity with its threshold. `stalled` is reversible; `abandoned` requires stronger evidence such as expired assignment plus failed contact/telemetry policy, explicit worker relinquishment, terminal provider loss, or authorized operator determination. No automated reassignment may occur.

A reassignment plan identifies the old/new attempts, proposed worker and capability match, ownership-transfer boundary, uncommitted/branch/PR reconciliation, prerequisite recheck, handoff evidence, rollback, and required operator authorization. Ownership cannot transfer until the prior assignment is closed or a narrowly scoped overlap is explicitly authorized.

## 9. Priority and workload planning

Implement a deterministic, versioned advisory priority policy. It must consider declared package/campaign priority, prerequisite readiness, critical-path contribution, lane capacity, worker capability and health, estimated active/wall-clock ranges from PL-0015, ownership/merge risk, aging, review capacity, and operator holds. Unknown estimates do not become zero and worker speed never overrides safety or authorization.

Tie-breaking is stable and documented. Starvation detection is explicit. Priority changes append decisions and reasons. Workload balancing respects worker concurrency, availability, lane boundaries, review bottlenecks, and risk; it must not maximize assignment count at the expense of dependencies or exclusive ownership.

An authorized operator may hold, release, reprioritize, authorize bounded overlap, select a worker, reject reassignment, or waive a non-safety advisory finding. Overrides require actor/authority, reason, scope, expiration, original decision, replacement decision, and audit event. An override cannot erase evidence, falsify completion, bypass a mandatory prerequisite without an explicit governed waiver, or grant authority the actor lacks.

## 10. Metrics

Produce read-only, windowed metrics with numerator, denominator, eligibility rules, sample size, time basis, evidence coverage, and provenance:

- eligible/queued/active/completed assignment counts;
- queue wait, acknowledged-to-start, active effort, review, integration, and wall-clock duration where evidenced;
- throughput by campaign/lane/worker class/provider (never an unsupported personnel ranking);
- completion, failure, stall, abandonment, reassignment, conflict, and merge-risk rates;
- concurrency utilization, blocked time, critical-path delay, estimate variance, and ownership-conflict prevention counts.

Do not double count multi-attempt packages or overlapping time intervals. Unknown boundaries remain unknown. Metrics cannot be used for punitive employment, compensation, reputation, or autonomous authorization decisions.

## 11. Completion verification and repository reconciliation

Worker/provider success is not package completion. Verification must evaluate the package's acceptance criteria against referenced commits/diffs, required tests, validation reports, review/PR state, completion receipt, ownership boundary, dependency version, and unresolved findings. It emits `verified`, `not_verified`, `conflicting`, `stale`, or `unknown` with per-criterion evidence; it never approves or merges.

Repository reconciliation accepts an offline repository/hosting snapshot describing refs, commits, worktrees, changed paths, branches, PRs, checks, reviews, receipts, and validation artifacts. It correlates them to campaign/package/assignment/attempt IDs; reports missing, duplicate, orphaned, divergent, superseded, stale, or conflicting evidence; and proposes no-op remediation instructions. It must detect work outside ownership, unexpected base/head, unrelated commits, duplicate PRs, and receipt claims unsupported by repository evidence. Network access, Git execution, and hosting mutations are prohibited.

## 12. PL-0014 and PL-0015 interface consumption

- **PL-0014 External Worker Telemetry:** consume only its published, provider-neutral assignment/observation/worker/snapshot contracts through a versioned adapter port. Preserve source provenance and freshness. Its absence or incompatible version yields explicit unknown health/activity, not a hard implementation dependency or invented event.
- **PL-0015 / WP-4214 Duration Estimation:** consume only its published read-only estimate result, confidence, bounds, components, freshness, and provenance through a versioned adapter port. The orchestrator must accept `not_estimable`, expired, low-confidence, or conflicting results and must not invoke calibration or rewrite estimates.

Contract tests use local synthetic fixtures for current published shapes and documented compatibility mappings. Neither dependency needs an implementation to exist. No private module import, direct database dependency, shared mutable store, or circular call is permitted.

## 13. Required staged artifacts

Under `collaboration/workstreams/WP-4215/`, create:

- `README.md` with authority, privacy, security, and isolation boundaries;
- pure orchestration-domain library and offline snapshot evaluator;
- schemas and examples for every Section 4 record;
- versioned lifecycle, ownership, dependency, priority, health, stall, abandonment, completion, and reconciliation policies;
- provider adapter ports plus PL-0014 and WP-4214 contract fixtures/adapters;
- wholly synthetic campaigns, workers, repositories, branches, PRs, telemetry, estimates, and failure fixtures;
- unit, property, schema, integration, deterministic replay, and no-outside-write tests;
- validation report, implementation completion receipt, and `INSTALL_HANDOFF.md` describing but not performing future integration.

## 14. Required tests and validation

Tests must cover:

- Codex, ChatGPT, future local, and future external worker registrations;
- lifecycle validity, idempotency, stale/out-of-order events, attempts, and reassignment;
- DAG validation, prerequisite gates, critical path, cycles, and graph-version drift;
- exact/glob/directory/case/rename/generated-path overlap and bounded overlap authorization;
- branch ownership, base/head drift, duplicate/conflicting PRs, overlapping diffs, and merge-risk ordering;
- stale versus stalled versus abandoned versus unknown classification;
- worker capability, health, concurrency, lane, and availability constraints;
- deterministic queue ordering, aging/starvation, priority overrides, and workload balancing;
- PL-0014 unavailable/stale/conflicting telemetry and adapter compatibility;
- WP-4214 not-estimable/low-confidence/stale estimates and adapter compatibility;
- completion verification with missing, contradictory, stale, and complete evidence;
- repository reconciliation with orphaned commits/branches/PRs, out-of-bound changes, and unrelated commits;
- metric denominators, evidence coverage, multi-attempt deduplication, and unknown durations;
- audit/provenance completeness, unauthorized override rejection, replay determinism, schema rejection, no network access, and no writes outside staged/temp paths.

Validation must run the staged suite twice and compare logical outputs, validate every schema/example/fixture, inventory changed paths, scan for secrets and real worker identities, and confirm no production/shared path changed. The report records exact commands, results, fixture counts, limitations, policy/schema/adapter versions, and a negative proof that no dispatch, Git, merge, or runtime behavior exists.

## 15. Completion and lifecycle gates

WP-4215 implementation is complete only when all staged artifacts exist, all required tests pass, validation evidence exists, and a complete implementation receipt identifies its commits and PR plus known limitations. Completion does not install the planner or authorize execution.

PL-0016 remains `Promoted` until the implementation is merged, required staged tests pass, validation evidence and implementation receipt exist, and an authorized lifecycle review closes it. Production integration always requires a separate install-handoff package.

## 16. Acceptance criteria

1. Sections 3–12 are represented in versioned schemas, pure staged logic, fixtures, and tests.
2. Exclusive file and branch ownership fails closed unless a bounded, authorized overlap exists.
3. Dependency, duplicate, stale, abandoned, branch, PR, and merge-risk findings are deterministic and evidence-backed.
4. Registration and adapter seams support Codex, ChatGPT, and future local/external workers without provider-specific lifecycle coupling.
5. PL-0014 and WP-4214 are consumed only through published, optional, versioned interfaces.
6. Completion verification and reconciliation distinguish worker success from verified package completion.
7. Overrides, decisions, transitions, corrections, and metrics preserve provenance and append-only audit history.
8. All implementation stays within `collaboration/workstreams/WP-4215/`; no production runtime, scheduler, dispatch, CLI, Git, or merge automation is created or modified.
9. A separate install-handoff is explicitly required and PL-0016 remains `Promoted` until Section 15 is satisfied.
