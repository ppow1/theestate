# Local Git Synchronization Assistant — Coordination Architecture

Status: Proposed for staged proof by WP-4217
Date: 2026-07-26
Decision scope: PL-0019 operator-coordination gap only

## Context and decision

The Estate already has Git behavior in the Operational Readiness Closure Controller, governed Publication Controller path, Merge Discovery, Post-Merge/Cleanroom Audit, Execution Control, and repository validation. Those systems own action, authority, validation, and durable operational evidence. They do not provide one operator explanation of a local checkout's synchronization choices.

Build a **read-only coordination assistant**, initially isolated under `collaboration/workstreams/WP-4217/`. It gathers immutable Git observations and existing controller projections, computes deterministic diagnostics/readiness/recommendations, and renders guidance. It performs no synchronization action. A later install package may wire its projection into existing CLI/Office surfaces and may delegate explicit fetch observation to an existing approved seam.

## Responsibility boundary

```text
configured repository target + immutable Git observations
  + Merge Discovery fetch evidence
  + Operational Readiness / Publication assessment
  + Post-Merge Audit / Execution Control / validation evidence
    -> read-only normalization
    -> deterministic relationship and conflict analysis
    -> readiness + recommendation decision table
    -> canonical assessment and existing-surface projection
```

The assistant owns only normalization and explanation. Git owns repository mechanics. Publication owns push authority/action. Operational Readiness owns managed fast-forward remediation and readiness cases. Merge Discovery owns remote discovery/fetch evidence. Audit owns post-merge verdicts and cleanroom lifecycle. Execution Control owns session admission. Repository validation owns validation verdicts.

## State model

Working state separates attached/detached/unborn HEAD, clean/dirty index and worktree, untracked/submodule summaries, and in-progress operations. Remote state separates configured remote, upstream binding, last successful fetch, current attempt, reachability, freshness, and remote-tracking object ID.

When ancestry is current and known, `rev-list --left-right --count HEAD...upstream` maps to synchronized `(0,0)`, ahead `(n,0)`, behind `(0,n)`, or diverged `(n,m)`. Missing refs, failed/stale fetch, shallow missing objects, or command failure yields unknown—not fabricated zeroes. Object IDs and merge-base anchor analysis against immutable inputs.

Readiness is multi-dimensional. Fast-forward, merge, rebase, and publication each receive their own verdict/reasons. Technical readiness never implies authorization. Synchronized repositories are not “ready to publish”; publication is not applicable. Dirty, detached, operation-in-progress, divergent, stale, or unreachable conditions remain explicit.

## Conflict prediction decision

Prefer read-only `git merge-tree` analysis against object IDs. It reads the object database without changing HEAD, refs, index, or worktree. Tool/version limitations, missing objects, binary/rename/submodule ambiguity, or stale remote observations yield an explicit unknown result.

Rebase prediction may require replay semantics. If read-only analysis is inadequate, use only a disposable isolated staging worktree/clone with fixed inputs and no production paths; never use the active checkout. Prediction reports confidence and candidate paths but never guarantees success or resolves conflicts.

## Safety decision table

| Observed state | Readiness direction | Safest guidance |
| --- | --- | --- |
| Clean, attached, synchronized | No synchronization needed | Continue work; no action performed. |
| Clean, attached, behind, no conflict predicted | Fast-forward technically ready | Review normal fast-forward through authorized workflow. |
| Clean, attached, ahead only | Publication may be technically possible | Send assessment to existing Publication Controller; verify authority. |
| Diverged | Merge/rebase review required | Inspect local commits and prediction; operator chooses policy. |
| Dirty | Synchronization not ready | Preserve and classify local work; do not stash/reset automatically. |
| Detached HEAD | Branch operations not ready | Preserve work and review intended branch before switching. |
| Missing upstream | Remote relationship unknown | Ask authorized operator to verify/configure tracking. |
| Fetch unreachable/stale | Remote conclusions unknown | Restore connectivity/credentials, then explicitly retry observation. |
| Operation in progress | New synchronization not ready | Finish or abort the existing operation deliberately. |
| Conflict predicted | Merge/rebase not ready for routine flow | Review affected paths and prepare manual resolution. |

Recommendations come from versioned data and contain no executable shell. Force push, reset, clean, routine stash, automatic checkout, automatic merge/rebase/pull/push, branch deletion, remote mutation, and conflict resolution are prohibited.

## Determinism, history, and provenance

Canonical assessments sort all diagnostic/recommendation/path collections and hash only stable evidence, decision-table/schema versions, object IDs, and normalized command outcomes. Observation timestamps and durations remain provenance but do not change the stable assessment ID.

History reuses the existing operational evidence mechanism selected during installation. Staging uses fixture-local JSONL solely to prove linking and replay. Records contain sanitized commands/results, versions, evidence IDs, producer, and previous assessment ID. They state observations and recommendations—not that synchronization occurred. This avoids another repository-state database.

## Failure and privacy posture

All subprocess calls use allowlisted argument arrays, explicit working directories, noninteractive credential settings, timeouts, and bounded output. Errors map to stable categories; raw credential-bearing URLs and stderr are redacted. Repository-relative conflict paths may be included under policy, but file content, diffs, credentials, environment secrets, and arbitrary paths are excluded.

Fetch failure preserves last-known evidence with a stale marker. Missing Git, unsupported commands, malformed output, unsafe paths/ownership, timeouts, and shallow/missing objects fail closed to unknown. The assistant never repairs a checkout in response.

## Alternatives rejected

| Alternative | Disposition | Reason |
| --- | --- | --- |
| New Git wrapper/one-command synchronizer | Reject | Duplicates Git and would blur mutation/authority boundaries. |
| New publication service | Reject | Governed publication already exists. |
| Automatic pull/rebase/merge | Reject | Operator intent and conflict policy cannot be inferred safely. |
| New repository state database | Reject | Existing evidence/history mechanisms must be reused. |
| Parse only `git status` prose | Reject | Locale/version instability and insufficient ancestry/provenance. |
| Predict by merging active checkout | Reject | Mutates operator state and violates isolation. |
| Treat cached remote refs as current | Reject | Produces false synchronized/ahead/behind claims after fetch failure. |

## Integration and rollback

WP-4217 proves everything under its isolated workstream with temporary repositories and local bare remotes. It makes no shared runtime or controller edit. A later install package must name public adapter seams, affected shared files/hashes, compatibility tests, authority routing, evidence retention, UI/CLI projection, and rollback. Rollback of staging is directory removal; production rollback removes only the assistant projection/adapters and leaves every governing controller unchanged.
