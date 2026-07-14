# Campaign 0550 — Local Engineering Department First Operational Slice

Status: Ready for implementation
Office owner: Chief Architect #5
Work-package range: WP-0548 through WP-0552
Repository: ppow1/theestate

## Objective

Deliver one production-grade, auditable local-engineering loop in the shortest practical time without creating duplicate Estate control planes.

The campaign must prove this exact institutional flow:

1. The Steward identifies a real engineering objective.
2. Helen defines the required roles, verifies available qualifications, and records a staffing decision.
3. Grace receives the staffed team and creates the governed operational assignment.
4. The Estate dispatch layer hands a bounded package to an external local-worker runtime under `A:\AI\Tools\EngineeringWorkerRuntime`.
5. The local worker executes in an isolated Git worktree.
6. Independent verification produces evidence and an accept, fail, or escalate result.
7. Grace records operational completion or escalation.
8. Chief Architect and Steward retain institutional acceptance authority.

## Settled office boundaries

### Helen — Personnel and hiring

Helen owns:

- role definitions;
- worker and candidate records;
- hiring or instantiation recommendations;
- qualification evidence;
- staffing readiness;
- assignment of available personnel to Grace.

Helen does not own scheduling, execution queues, runtime supervision, package acceptance, or code integration.

### Grace — Operations

Grace owns:

- objective intake;
- operational assignment;
- sequencing and dispatch requests;
- runtime status and blocker tracking;
- retry and escalation decisions within delegated authority;
- evidence collection and delivery status.

Grace does not hire personnel, redefine qualifications, merge code, override Traffic Controller, or declare institutional acceptance.

### Chief Architect #5

Chief Architect #5 owns execution-provider architecture, provider contracts, local-first engineering boundaries, qualification evidence architecture, and recommendation-only routing. This campaign must not create a second scheduler, queue, registry, dispatch authority, or provider control plane.

## Runtime boundary

The production local worker runtime belongs under:

`A:\AI\Tools\EngineeringWorkerRuntime`

Raw worktrees and execution evidence belong outside the Estate repository, preferably under:

- `A:\AI\EngineeringWorktrees`
- `A:\AI\EngineeringRuns`

The Estate retains only:

- governed worker and staffing records;
- package and assignment records;
- provider capability, capacity, and health references;
- evidence hashes and canonical paths;
- qualification summaries;
- dispatch and acceptance decisions.

## Work-package order

Read and implement in numeric order:

1. WP-0548 — Helen Engineering Workforce and Staffing Contract
2. WP-0549 — External Local Engineering Worker Runtime
3. WP-0550 — Grace Local Engineering Operations Integration
4. WP-0551 — Worker Qualification and Eligibility Evidence
5. WP-0552 — First Closed-Loop Local Engineering Demonstration

## Campaign constraints

- Production-grade implementation; no disposable MVP path.
- Reuse existing Helen, Grace, Dispatch, Traffic Controller, worker-assignment, provider-evidence, validation, and audit infrastructure.
- No direct automatic merge to `main`.
- No local agent may alter protected Estate areas outside a package contract.
- No cloud requirement for the local execution path.
- No automatic model download.
- PowerShell intended for the Steward begins with `CLS`.
- Where practical, diagnostic summaries are copied to the clipboard.
- Stop and report any architectural contradiction rather than inventing authority.

## Campaign acceptance

The campaign is complete only when one real bounded Estate package is:

- staffed by Helen;
- assigned and dispatched by Grace;
- executed by a local worker from `A:\AI\Tools\EngineeringWorkerRuntime`;
- isolated in a dedicated worktree;
- independently validated;
- preserved with immutable evidence;
- returned to Grace with a governed result;
- available to Chief Architect and Steward for final acceptance.

## Codex campaign handoff

Read every package completely before changing code. Implement strictly in numeric order on one coherent campaign branch and one pull request. Preserve settled systems and stop on contradiction. Report implemented packages, files changed, tests, external runtime paths created, evidence produced, blockers, and the exact command for the first closed-loop demonstration.