# PL-0048 — Canonicalize Estate Stream Deck Runtime Source and Deployment

Status: Captured
Priority: High
Category: Operator Deck / Runtime Reproducibility / Repository Governance
Originator: Pat / Steward
Date Captured: 2026-08-11
Target Milestone: After current Grace/Stream Deck functional debugging is stable enough to address source-of-truth and reproducible deployment without disrupting the working installed runtime

## Idea

Canonicalize the Estate Stream Deck implementation currently living outside `A:\theestate` so a clean checkout or rebuild can reproduce the installed runtime without relying on mutable external runtime trees as the only source of truth.

The future work should identify the repository-owned canonical source location for the Estate Stream Deck plugin/runtime implementation, reconcile the currently working external implementation with that source, establish a reproducible build/deploy/install path, and document the source-of-truth and deployment contract.

Important working implementation has recently been identified under external paths including:

- `A:\AI\Tools\EstateStreamDeckPlugin`
- `A:\AI\Tools\EstateStreamDeckMVP\Core`

Examples previously identified include:

- `src/status.js`
- `src/plugin.js`
- `Estate-Service-Lib.ps1`
- `Estate-Service-Config.ps1`
- `Get-EstateServiceStatus.ps1`

The repository commit that documented and tested lifecycle hardening did not itself contain all of the working implementation. This creates a reproducibility, recovery, and ownership risk even though the installed runtime is currently working.

## Why This Matters

A clean checkout of `A:\theestate` may not reproduce the installed Stream Deck runtime today.

That creates several related risks:

- a rebuild, reinstall, or cold recovery may lose fixes that exist only in mutable external runtime trees;
- source-of-truth ownership is ambiguous;
- installed runtime and repository state can drift;
- future engineering may regress behavior because repository state does not fully represent the working implementation;
- a future engineer may be unable to determine which files are authoritative, generated, deployed, or locally mutated.

The goal is reliability and reproducibility, not cosmetic repository cleanup.

## Why It Is Parked

This work is important, but it is not the current active priority.

It is being parked specifically to reduce scope creep while preserving a reliability/reproducibility problem that clearly needs deliberate follow-up.

Current Grace/Stream Deck functional debugging should continue without being blocked by a source-tree migration. The currently working installed runtime should remain undisturbed until this item is intentionally promoted and given a bounded work package.

## Promotion Condition

Promote when current Grace/Stream Deck functional debugging is stable enough to address source-of-truth and reproducible deployment without disrupting the working installed runtime.

When promoted, the work should begin with an inventory and comparison of canonical repository state versus the known-good external runtime, then define the smallest safe migration/deployment contract before changing installed files.

## Explicit Non-Action

This item is parked.

Do not, as part of capturing or maintaining this Parking Lot item:

- move files;
- rewrite the Stream Deck plugin;
- modify runtime/plugin files;
- start or stop services;
- disturb the working installed runtime;
- touch GPUs;
- touch Open WebUI, Grace, RGW, SillyTavern, ComfyUI, or databases;
- let this block current Grace/Stream Deck debugging;
- turn this into a broad repository restructuring project;
- refactor merely for cleanliness.

Preserve the currently working runtime until canonicalization is deliberately scheduled.

## Target Outcome

When this item is eventually promoted and completed, a future engineer should be able to answer, from repository-owned documentation and implementation:

1. Where does the canonical Estate Stream Deck plugin/runtime source live?
2. Which files are authoritative source versus generated or deployed artifacts?
3. How are installed runtime artifacts produced from canonical source?
4. How are they deployed or reinstalled safely?
5. How can a clean checkout regenerate or deploy the installed Stream Deck runtime?
6. How can installed files be verified against canonical source?
7. What prevents undocumented mutable runtime files from becoming the only source of truth again?
8. What is the documented source-of-truth and deployment contract?

Migration acceptance must verify that no currently working behavior is lost.

## Intended Future Scope

When promoted, keep the effort narrow and evidence-driven:

- identify the canonical repository-owned source location for Estate Stream Deck plugin/runtime implementation;
- inventory the currently working external files and classify them as authoritative, generated, deployed, configuration, or runtime-only;
- reconcile working external files with canonical source without assuming either side is complete;
- preserve known-good behavior while migrating ownership;
- establish a reproducible build/deploy/install path;
- add a verification mechanism that can detect repository/runtime drift;
- document the canonical source-of-truth and deployment contract;
- avoid unrelated cleanup or generalized repository reorganization.

## Related Evidence

- Working external implementation paths observed during recent Stream Deck repair:
  - `A:\AI\Tools\EstateStreamDeckPlugin`
  - `A:\AI\Tools\EstateStreamDeckMVP\Core`
- Representative implementation files observed outside the canonical repository:
  - `src/status.js`
  - `src/plugin.js`
  - `Estate-Service-Lib.ps1`
  - `Estate-Service-Config.ps1`
  - `Get-EstateServiceStatus.ps1`
- Recent lifecycle-hardening repository work documented/tested behavior without containing all working implementation source.
- Related repository-governance concern: PL-0030, Estate directory/worktree consolidation, but this item must remain narrower and must not become a general repository restructuring effort.
- Existing Stream Deck-related Parking Lot items should be treated as adjacent context rather than justification to broaden scope.
- Canonical Parking Lot process: `AI_COMMUNICATION_HINTS.md`.
