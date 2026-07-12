# WP-0539 — External Repository Access and Workspace Runtime

Status: Pending  
Execution Mode: SERIES  
Owner: Office of Chief Architect / Engineering Operations  
Execution Target: Codex  
Classification: Estate Internal  
Priority: Critical

## Depends On

- WP-0536 — Engineering Project Intake and Mobilization Runtime
- WP-0537 — Engineering Workforce Role Catalog and Staffing Plan Runtime
- WP-0538 — Local Engineering Worker Provisioning Runtime

## Objective

Implement a production-grade runtime that safely connects an authorized Estate engineering project and its provisioned workers to one or more external source repositories without copying credentials into Estate records or bypassing repository governance.

## Required Work

1. Define repository-access contracts covering repository identity, owner, URL, default branch, permitted operations, local workspace root, authentication method reference, classification, branch policy, protected paths, build/test commands, artifact paths, and retention.
2. Verify access through read-only probes before any mutation.
3. Create deterministic local workspaces and branches for assigned workers; prevent two workers from silently sharing a mutable checkout.
4. Support private and public Git repositories, detached source archives, local-only repositories, submodules, large-file storage, and multiple repositories per project.
5. Integrate with existing GitHub, work-package, execution-session, lease, cancellation, recovery, and validation systems.
6. Record repository and workspace evidence without storing secrets, tokens, SSH keys, or credential payloads.
7. Enforce allowlisted roots, path traversal protection, repository identity confirmation, clean-worktree checks, branch ownership, and safe cleanup.
8. Add workspace lifecycle states: REQUESTED, ACCESS_CHECK, READY, LEASED, ACTIVE, DIRTY, BLOCKED, RECOVERING, ARCHIVED, and RELEASED.
9. Preserve commit, branch, diff, test, artifact, and handoff lineage for every engineering assignment.
10. Expose CLI and machine-readable operations for inspect, authorize-reference, prepare, lease, status, recover, archive, and release.

## Production Requirements

- Windows-safe paths and long-path handling.
- Idempotent workspace preparation.
- Atomic lease and ownership records.
- Crash recovery with dirty-worktree preservation.
- No destructive reset, clean, force-push, or branch deletion without explicit governed authorization.
- Concurrency tests across multiple workers and repositories.
- Structured failure reports suitable for Helen, Grace, Engineering, Ingrid, and the Office.

## Acceptance Tests

1. An authorized private external repository can be verified and prepared without placing credentials in project records.
2. Unauthorized, mismatched, or inaccessible repositories block before worker execution.
3. Parallel workers receive isolated workspaces and branches.
4. Crash recovery preserves uncommitted work and identifies its owner.
5. Branch, commit, test, and artifact lineage remains auditable through completion.
6. Unsafe paths, credential leakage, destructive operations, and repository identity drift are rejected.
7. Existing dispatch and execution-session machinery is reused rather than duplicated.
8. Unit, integration, concurrency, recovery, security, and Windows end-to-end tests pass.

## Deliverables

- repository-access and workspace schemas;
- workspace lifecycle runtime and CLI;
- authentication-reference adapter;
- lease, recovery, archive, and release handlers;
- tests, fixtures, documentation, validation recipe, and completion receipt.

## Constraints

- Do not create a second source-control platform, credential store, dispatch system, or execution-session runtime.
- Do not clone or mutate a repository before authority and identity checks pass.
- Do not discard dirty work during recovery or cleanup.

## Completion Standard

WP-0539 is complete only when authorized external repositories can be safely prepared, isolated, leased, recovered, audited, and released for local engineering workers under Windows without credential leakage, workspace collisions, or destructive implicit behavior.