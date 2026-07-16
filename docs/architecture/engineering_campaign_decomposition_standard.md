# Engineering Campaign Decomposition Standard

Status: Gate B contract
Campaign: CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION
Work package: WP-0671

## Decomposition outcome

The Chief Architect decomposes an accepted campaign into work packages, the sole unit of Engineering work. Each package MUST use the canonical repository convention and have exactly one primary campaign. A package is atomic when one bounded branch can deliver and validate it, one owner can explain its result, and rollback does not require guessing which unrelated changes belong to it.

## Required package fields

Each package records: literal package and primary campaign IDs; status; authority owner; execution lane; objective; in-scope and non-goals; required reading; typed dependencies; owned paths and prohibited paths; branch owner and release event; deliverables; risk; readiness evidence; validation recipe; rollback; completion evidence; acceptance authority; and integration checkpoint.

Dependencies use stable IDs and one of `blocks`, `finish_to_start`, `start_to_start`, `evidence_required`, or `approval_required`. A dependency is machine-checkable when it names a canonical record, expected state and deterministic check. Otherwise set `verification: manual`, name the verifying authority and required signed/durable decision. Missing, cyclic, conflicting or unknown evidence is not satisfied.

## Package sizing and atomicity

Split a package when it has independent acceptance decisions, unrelated rollback units, more than one primary campaign, incompatible execution lanes, or owned-file overlap that cannot be serialized. Keep coupled schema/consumer edits together only when separate commits would leave the repository invalid and one validation recipe proves the boundary. Discovery must not conceal implementation.

A package may not derive absent scope at execution. Ambiguity affecting authority, protected data, owned paths, dependency order or acceptance returns the package to planning.

## Shared-file collision control

Before readiness, every package declares exact files or bounded globs it owns. The campaign graph maintains a collision table with package IDs, paths, planned order, integration checkpoint and resolver. Overlaps require one of:

1. combine inseparable work into one atomic package;
2. sequence packages with an explicit dependency and rebase checkpoint; or
3. assign a shared integration package/owner after upstream branches merge.

Parallel packages MUST NOT own the same mutable file. Generated files name their source and regeneration owner. The Chief Architect resolves architectural collisions; the branch owner does not silently broaden scope.

## Branch and integration ownership

One implementation branch belongs to one package and one owner at a time. The package records branch naming rule, base commit, allowed paths and release event (`PR closed`, `merged`, `cancelled`, or explicit reassignment). Retries use new attempt identity without overwriting prior evidence. Commits and PRs carry campaign/package IDs.

Integration checkpoints occur after prerequisite PRs are accepted/merged as defined by the campaign. Passing validation does not merge or accept work. The Chief Architect reviews architecture and package acceptance; canonical post-merge readiness remains separate.

## Validation and completion evidence

Before execution, each package supplies a reproducible validation recipe containing exact commands, environment/preconditions, required versus observational checks, expected artifacts, failure semantics and evidence locations. Every recipe binds evidence to branch and commit. Material changes require rerun evidence.

Completion requires a receipt that records campaign/package IDs, execution/acceptance/integration states separately, branch, commits/PR, deliverables, commands and results, evidence digests/paths, known limitations, rollback instructions, actor and timestamps. A receipt reports history; it does not self-accept or supersede canonical validation.

## Rollback and interruption

The package identifies reversible commits/artifacts, data or migration safeguards, restore command/procedure, verification and rollback authority. Protected or irreversible work requires an approved recovery plan before execution. On interruption, preserve working state and evidence, release provider reservations through their canonical mechanism, and retain branch ownership until an authorized release event.

## Decomposition review checklist

- one primary campaign and valid parent authority;
- no hidden scope or unrelated deliverables;
- dependency graph is acyclic and verification is explicit;
- owned paths have no uncontrolled parallel collision;
- branch ownership and integration order are explicit;
- validation binds to the delivered commit;
- rollback is actionable;
- receipt and acceptance evidence are specified.
