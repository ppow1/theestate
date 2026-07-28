# PL-0030 — Estate Directory and Worktree Consolidation

## Idea

Consolidate the multiple Estate directory structures that have accumulated on the development drive during testing, work-package execution, and repeated local experimentation into one intentional canonical Estate directory structure.

The current environment includes the primary Estate checkout plus additional worktree- or test-oriented directories with names such as `theestate-wp####` and other temporary or duplicated Estate roots. These structures were useful for isolated implementation and validation, but they now create ambiguity about which checkout is authoritative, which services are running from which path, where unmerged work exists, and which directories can be retired safely.

The proposal is to establish one canonical Estate root for ordinary operation, retain only the minimum worktrees needed for active governed work, and create a controlled consolidation process that inventories, reconciles, archives, merges, or removes the remaining directory structures without losing code, reports, configuration, runtime data, or uncommitted changes.

## Why It Is Parked

The Grace runtime integration and related Open WebUI work are currently the active focus. Directory consolidation would interrupt that momentum and carries avoidable risk if attempted without a complete inventory of branches, worktrees, modified files, running processes, service launch paths, local-only configuration, and untracked artifacts.

This item is therefore being preserved for deliberate follow-up rather than acted on during the current integration effort.

## Proposed Scope

When promoted, the work should include:

1. Inventory every Estate-related directory on the relevant drive, including the canonical checkout, Git worktrees, abandoned test copies, deployment copies, generated artifact directories, and any directory used by running services.
2. Record for each directory:
   - absolute path;
   - Git repository and worktree identity;
   - branch and HEAD commit;
   - clean/modified/untracked state;
   - ahead/behind relationship to the authoritative branch;
   - active processes or services launched from that path;
   - local configuration, reports, databases, logs, and runtime artifacts not represented in Git;
   - disposition recommendation.
3. Define the canonical Estate root and the approved purpose and naming standard for any retained worktrees.
4. Reconcile valuable changes into the governed repository workflow before removing any directory.
5. Preserve required local-only runtime and deployment data in explicitly designated Estate locations rather than leaving it embedded in disposable worktrees.
6. Update launch scripts, environment variables, shortcuts, service definitions, scheduled tasks, Open WebUI integration paths, and operator documentation so they point to the canonical structure.
7. Remove or archive obsolete directories only after verification that no running process, unmerged change, required artifact, or recovery dependency remains.
8. Produce a final directory map and operator-facing recovery note showing the canonical checkout, approved worktree location, runtime-data locations, and rules for future temporary worktrees.

## Governing Principles

- Inventory before mutation.
- Never assume a similarly named directory is disposable.
- Do not delete a worktree with uncommitted, untracked, unpushed, or unreviewed work.
- Preserve Git history and governed merge boundaries.
- Separate source checkout, runtime data, generated reports, caches, and deployment state intentionally.
- Keep active work isolated when needed, but prevent temporary worktree names from becoming permanent operational roots.
- Prefer one canonical operational Estate path and a predictable subordinate location for temporary worktrees.
- Validate all service and script references before and after consolidation.
- Provide rollback evidence before destructive cleanup.

## Candidate End State

A likely target pattern is:

- one canonical Estate checkout used for normal operation and production-facing scripts;
- one clearly named parent directory for temporary governed worktrees;
- separate canonical locations for runtime data, reports, local secrets, caches, and generated artifacts;
- no long-lived service depending on an ad hoc `theestate-wp####` path;
- a documented creation, promotion, merge, and retirement lifecycle for future worktrees.

The exact paths must be selected only after the inventory confirms current dependencies.

## Promotion Condition

Promote this item when the current Grace/Open WebUI integration campaign is stable enough to pause, and when there is time to perform a complete read-only inventory before any consolidation or deletion.

Promotion should also occur sooner if path ambiguity causes another service restart, deployment, merge, or validation failure, or if the Steward cannot reliably determine which Estate directory is authoritative.

## Explicit Non-Action

Capturing this proposal does not authorize moving, merging, renaming, archiving, or deleting any Estate directory or worktree.

Do not stop services, remove worktrees, discard local changes, rewrite launch paths, or consolidate runtime data until this idea is intentionally promoted into governed work with an approved inventory and rollback plan.

## Related Evidence

- Recent Grace runtime and Open WebUI integration work used the isolated worktree `A:\theestate-wp4233` while operator commands were also run from `A:\theestate\tools\operator-deck`.
- The running Residential Gateway was previously launched from a worktree-specific source path, demonstrating that service behavior can depend on which Estate directory is active.
- Repeated testing has created multiple Estate directory structures whose authority and disposition should be resolved systematically rather than manually or opportunistically.
