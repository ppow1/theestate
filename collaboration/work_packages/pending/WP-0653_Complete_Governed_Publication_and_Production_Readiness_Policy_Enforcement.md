# WP-0653 — Complete Governed Publication and Production Readiness Policy Enforcement

## Status

Pending implementation.

## Owner

Office of Chief Architect, implemented through Engineering in the existing Operational Readiness Closure Controller and Estate Operations Runtime.

## Objective

Repair the existing canonical Operational Readiness Closure Controller in place so that controller-authored repository mutations are not considered complete until they are published through an authorized non-destructive workflow and verified on the configured upstream, and so that `operationally_ready` cannot be declared from a trivial default compile check and a single zero-duration observation when the target policy requires stronger evidence.

This is a defect repair and production hardening of the existing controller. Do not create a replacement controller, second readiness engine, parallel publication service, duplicate policy registry, new scheduler, or new institutional structure.

## Proven Defect

WP-0652 live acceptance proved that the controller can transactionally update and commit the Activation Ledger while leaving the local checkout clean. It also exposed two remaining defects:

1. The controller-authored commit remained local and left `main` ahead of `origin/main`; the controller nevertheless declared the readiness case `operationally_ready`.
2. The case used a default validation recipe that only compiled one module and an observation policy of one immediate cycle, zero elapsed seconds, no health checks, and no restart evidence.

The controller must not declare operational readiness while its own required canonical mutation is unpublished or while the applicable target policy has not supplied and satisfied meaningful live validation and observation gates.

## Required Outcome

The repaired controller must autonomously complete this path for authorized repository-backed remediations:

1. Assess the target and verify a clean, authorized managed checkout.
2. Apply the exact deterministic mutation.
3. Commit the mutation with case and evidence attribution.
4. Publish the commit to the configured upstream and branch through an authorized fast-forward-safe workflow.
5. Fetch and verify that the upstream branch contains the authored commit.
6. Verify the local checkout is clean and synchronized.
7. Record complete publication evidence.
8. Reassess the readiness case.
9. Execute the declared target-specific live validation recipe.
10. Enforce the declared target-specific observation policy.
11. Declare `operationally_ready` only after every applicable gate is proven.

## Governed Publication Contract

Extend the existing controller with one deterministic publication handler or transactional continuation inside the existing repository-mutation workflow.

The publication behavior must:

- execute only when target policy explicitly authorizes publication;
- use the target's configured upstream and base branch;
- refuse dirty, detached, divergent, ambiguous, unauthorized, or non-fast-forward conditions;
- never force-push, force-reset, rewrite history, discard work, delete branches, or bypass protection;
- record the pre-publication local HEAD, upstream HEAD, ahead/behind state, command, stdout, stderr, exit code, and timestamp;
- push only the exact controller-authored commit chain intended for the configured base branch;
- fetch after push and verify the upstream branch contains the controller-authored commit by ancestry;
- verify local and upstream synchronization after publication;
- remain idempotent when the commit is already present upstream;
- stop with an exact bounded blocker when credentials, branch protection, remote rejection, divergent history, or missing authority prevents publication;
- never treat a local-only commit as a completed canonical mutation.

A readiness case must remain active or blocked, not ready, until required publication verification succeeds.

## Existing Local Commit Recovery

The implementation must safely handle the live acceptance residue in which local `main` contains controller-authored commit:

`8b4a6b0b98e36c337d98374127a8783053e6fce0`

while `origin/main` does not.

Do not hard-code this commit into production logic. Add generic recovery behavior that recognizes an attributable controller-authored local commit, verifies that it is the only unpublished fast-forward-safe change, publishes it if authorized, verifies upstream containment, and resumes the existing case.

## Readiness Policy Enforcement

Remove the ability to reach `operationally_ready` through an undeclared or trivial fallback policy for production targets.

For each target, require explicit canonical metadata for applicable gates:

- validation recipe;
- live target path;
- required reachability or health probes;
- minimum production runtime cycles;
- minimum elapsed observation time;
- required restart events when applicable;
- required Scheduled Task, service, PID, lock, heartbeat, revision, and root checks where applicable;
- publication requirement for controller-authored canonical mutations;
- acceptance authority.

Default posture for a production target is deny readiness when required policy is missing.

A lightweight compile-only recipe may be used for syntax validation, but it must not by itself qualify a production target as operationally ready unless the target policy explicitly states that this is sufficient and records why.

A single instantaneous observation with zero elapsed duration, no health checks, and no restart evidence must not satisfy a production policy unless the target explicitly declares those gates not applicable.

## Verdict Integrity

The durable verdict must derive its fields from verified evidence, including:

- required merge commit contained by deployed target;
- controller-authored mutation commit, when any;
- publication required boolean;
- publication status;
- upstream branch and verified upstream commit;
- local/upstream ahead-behind state after publication;
- deployed revision;
- activation evidence;
- validation policy and results;
- observation policy and results;
- unresolved findings;
- operational-readiness boolean;
- institutional acceptance boolean, which remains false unless explicitly granted by proper authority.

Do not infer publication, synchronization, deployment, validation, observation, or activation merely from controller state.

## Office and CLI Visibility

Extend the existing Office and CLI projections to show:

- local HEAD;
- upstream HEAD;
- ahead/behind state;
- unpublished controller-authored commits;
- publication authorization and status;
- exact publication blocker;
- validation policy completeness;
- observation policy completeness;
- remaining readiness gates;
- next automatic action.

Do not create a second dashboard or control surface.

## Required Tests

Add focused tests proving at minimum:

1. Authorized clean publication pushes an attributable controller-authored commit and verifies it upstream.
2. Already-published commits are handled idempotently.
3. Dirty, detached, divergent, wrong-branch, and unauthorized repositories are refused without mutation.
4. Remote rejection leaves truthful evidence and does not mark the case ready.
5. Local-only canonical mutation prevents readiness.
6. Missing production validation or observation policy prevents readiness.
7. Compile-only validation plus zero-duration observation does not satisfy the default production policy.
8. Explicit target policy can declare non-applicable gates with recorded rationale.
9. Verdict fields reflect verified upstream, validation, and observation evidence.
10. Existing case recovery publishes a safe attributable local controller commit and resumes progression.
11. No institutional acceptance is granted automatically.
12. No force push, reset, discarded work, arbitrary shell execution, duplicate scheduler, or duplicate readiness system is introduced.

## Live Windows Acceptance

Run live acceptance on the Windows Estate target using the existing readiness case or a new automatically discovered merged work package.

The acceptance must prove:

- the controller detects the unpublished attributable local commit or creates a new governed repository mutation;
- the controller publishes through the authorized workflow without manual `git push` by the Steward;
- `origin/main` contains the authored commit afterward;
- local and upstream branches are synchronized;
- the checkout is clean;
- readiness does not advance until publication is verified;
- explicit live validation and observation policy is loaded;
- all required live checks are executed and evidenced;
- the case reaches `operationally_ready` only when every declared gate passes;
- the controller stops with a precise blocker if publication or policy requirements cannot be satisfied.

## Completion Evidence

Produce:

- updated controller implementation;
- updated operational-target metadata handling;
- updated Office/CLI projection;
- focused unit and integration tests;
- live Windows acceptance report;
- canonical validation recipe;
- completion receipt with exact files, commands, evidence paths, publication result, policy gates, and remaining blockers.

## Explicit Constraints

Do not:

- create another controller or publication engine;
- create another scheduler, queue, registry, ledger, Office, or dashboard;
- force-push or force-reset;
- discard local work;
- bypass branch protection;
- fabricate credentials or authority;
- execute arbitrary generated shell commands;
- weaken validation or observation requirements merely to obtain a passing verdict;
- mark a case ready while a required local commit is unpublished;
- grant institutional acceptance automatically.

## Success Criteria

WP-0653 is complete only when the existing canonical controller can autonomously publish its authorized repository-backed mutations, verify upstream containment and synchronization, enforce explicit production validation and observation policy, and produce a truthful operational-readiness verdict without manual Steward Git intervention.

## Work Package Handoff

Work package filename:
`WP-0653_Complete_Governed_Publication_and_Production_Readiness_Policy_Enforcement.md`

Repository path:
`collaboration/work_packages/pending/WP-0653_Complete_Governed_Publication_and_Production_Readiness_Policy_Enforcement.md`

Codex must use the GitHub repository and current `main` branch as the source of truth.