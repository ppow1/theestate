# ADR-0003: Estate Work Package State Machine Proposal

## Status
Proposed — pending Chief Architect review

## Context

ADR-0002 proposes a durable Work Package Registry that records each work package as an auditable institutional object. The next architectural requirement is a canonical state machine that lets work packages move through consistent, reviewable states without making transient prompts, local worker notes, or operations-board rows the source of truth.

This proposal defines the state vocabulary, transition rules, and office or role authority needed for registry-backed work packages. It is intentionally architecture-only: it does not implement state automation, does not create a registry schema, and does not redefine Estate lifecycle states outside the work-package domain.

## Decision Drivers

- Work package status must be durable, auditable, and reviewable.
- Architecture-first and governance-adjacent work must not be implemented before Chief Architect authorization.
- Codex needs clear boundaries for when it may accept, execute, complete, or stop work.
- Merge and validation gates must distinguish worker completion from architectural verification, merge authorization, and operational validation.
- The model must support blocked, parked, superseded, and closed outcomes without hiding incomplete work.

## Proposed State Definitions

| State | Meaning | Typical owner while in state |
|---|---|---|
| `proposed` | A work package idea or request exists but is not yet approved for scheduling or execution. | Steward, Chief Architect, Alfred, or originating office |
| `approved` | The work package is accepted as valid Estate work, but is not necessarily ready for a worker. | Steward or Chief Architect |
| `pending` | Approved work is waiting in a queue for dependency clearance, prioritization, or assignment. | Alfred or designated coordinator |
| `assigned` | A specific worker, resident, office, or execution lane has been assigned accountability. | Alfred, Steward, or coordinator |
| `in_progress` | The assigned executor has started work. | Assigned worker or office |
| `codex_done` | Codex has completed its assigned implementation or architecture artifact and produced required completion evidence. This is not merge approval. | Codex |
| `ca_review_pending` | Work awaits Chief Architect review, usually for architecture, governance, Class B+ merge risk, or review-gated implementation. | Chief Architect office |
| `ca_verified` | Chief Architect review accepted the work or architecture, possibly with conditions. This is not automatically a merge. | Chief Architect office |
| `merge_authorized` | The authorized office has approved merge or promotion into the relevant institutional location. | Steward or delegated merge authority, often after CA verification |
| `merged` | The approved changes have been merged or promoted to the authoritative repository or institutional location. | Maintainer, Steward, or merge executor |
| `validation_pending` | Merged or promoted work is awaiting operational validation or post-merge checks. | Audit, Operations, or validation owner |
| `operationally_validated` | Required post-merge validation has passed and the work is accepted as operationally valid. | Audit, Operations, or Steward |
| `blocked` | Progress cannot continue because an explicit dependency, decision, access, review, or environment requirement is unavailable. | Current owner plus blocker-resolving office |
| `parked` | Work is intentionally paused without being rejected or superseded. It may be resumed later by an authorized office. | Steward, Chief Architect, or Alfred |
| `superseded` | Work is replaced by another package, decision, artifact, or approach. It should not continue except for archival closure. | Steward or Chief Architect |
| `closed` | The package is terminally complete, cancelled, superseded, or administratively ended with final rationale recorded. | Steward, Chief Architect, or authorized coordinator |

## Transition Authority Model

Authority should be recorded as the office or role that triggers a transition, not merely the person or tool that edits a file. Automation may later enforce this model, but this ADR only proposes the rule set.

| From | To | Authorized trigger role or office | Required evidence or condition |
|---|---|---|---|
| `proposed` | `approved` | Steward or Chief Architect | Approval decision, source request, and classification are recorded. |
| `proposed` | `parked` | Steward, Chief Architect, or Alfred | Rationale for deferral is recorded. |
| `proposed` | `superseded` | Steward or Chief Architect | Superseding package, decision, or artifact is identified. |
| `proposed` | `closed` | Steward or Chief Architect | Rejection or administrative closure rationale is recorded. |
| `approved` | `pending` | Alfred, Steward, or designated coordinator | Package is accepted into the work queue. |
| `approved` | `ca_review_pending` | Steward, Chief Architect, or Alfred | Architecture-first, Class B+, or review-gated package requires CA review before execution. |
| `approved` | `parked` | Steward or Chief Architect | Approved work is intentionally deferred. |
| `pending` | `assigned` | Alfred, Steward, or designated coordinator | Assignee and execution lane are recorded. |
| `pending` | `blocked` | Alfred, Steward, Chief Architect, or assigned coordinator | Blocking dependency or decision is recorded. |
| `pending` | `parked` | Steward, Chief Architect, or Alfred | Queue item is paused by explicit decision. |
| `assigned` | `in_progress` | Assigned worker or assigned office | Work start is acknowledged. |
| `assigned` | `blocked` | Assigned worker, Alfred, Steward, or Chief Architect | Assignee cannot proceed and identifies blocker. |
| `assigned` | `pending` | Alfred, Steward, or coordinator | Assignment is withdrawn or requeued. |
| `in_progress` | `codex_done` | Codex | Required completion artifact, changed files, checks, limitations, and review readiness are recorded. |
| `in_progress` | `ca_review_pending` | Assigned worker, Chief Architect, or Steward | Work requires CA review before continuing or after architecture artifact completion. |
| `in_progress` | `blocked` | Assigned worker, Alfred, Steward, or Chief Architect | Blocking condition is recorded. |
| `in_progress` | `parked` | Steward or Chief Architect | Work is paused by governance or priority decision. |
| `codex_done` | `ca_review_pending` | Codex, Alfred, Steward, or merge coordinator | Completion evidence exists and review is requested. |
| `codex_done` | `blocked` | Chief Architect, Audit, Steward, or merge coordinator | Completion evidence is missing or merge/review cannot proceed. |
| `ca_review_pending` | `ca_verified` | Chief Architect | Review decision accepts the work, with conditions if any. |
| `ca_review_pending` | `blocked` | Chief Architect | Required correction, missing context, or unresolved governance issue is recorded. |
| `ca_review_pending` | `parked` | Chief Architect or Steward | Review is intentionally deferred. |
| `ca_review_pending` | `superseded` | Chief Architect or Steward | Another package or decision replaces the reviewed item. |
| `ca_verified` | `merge_authorized` | Steward or delegated merge authority | Merge conditions are satisfied and approval to merge is recorded. |
| `ca_verified` | `validation_pending` | Chief Architect, Steward, or validation owner | Architecture artifact requires validation rather than code merge, or merge is not applicable. |
| `ca_verified` | `closed` | Chief Architect or Steward | Architecture-only package is complete and no merge/validation action remains. |
| `merge_authorized` | `merged` | Maintainer, Steward, or authorized merge executor | Merge or promotion event is recorded. |
| `merge_authorized` | `blocked` | Maintainer, Steward, Audit, or Chief Architect | Merge cannot proceed because of conflict, failing check, or policy issue. |
| `merged` | `validation_pending` | Maintainer, Steward, Audit, or operations owner | Post-merge validation is required. |
| `merged` | `closed` | Steward or authorized coordinator | No separate operational validation is required and final record is complete. |
| `validation_pending` | `operationally_validated` | Audit, Operations, Steward, or designated validation owner | Required validation evidence passes. |
| `validation_pending` | `blocked` | Audit, Operations, Steward, or validation owner | Validation cannot complete or fails with required remediation. |
| `operationally_validated` | `closed` | Steward, Audit, Operations, or authorized coordinator | Final completion is recorded. |
| `blocked` | Prior non-terminal state | Blocking office, Steward, Chief Architect, Alfred, or assigned coordinator | Blocker is resolved and the previous actionable state is recorded. |
| `blocked` | `parked` | Steward or Chief Architect | Blocked work is intentionally paused. |
| `blocked` | `superseded` | Steward or Chief Architect | A new package or decision replaces the blocked work. |
| `parked` | `pending` | Steward, Chief Architect, or Alfred | Work is resumed into the queue. |
| `parked` | `ca_review_pending` | Steward or Chief Architect | Resumed work first requires CA review. |
| `parked` | `superseded` | Steward or Chief Architect | Deferred work is replaced. |
| `superseded` | `closed` | Steward, Chief Architect, or authorized coordinator | Supersession record is complete. |

## Guardrails

- `codex_done` means worker completion only; it must not imply `ca_verified`, `merge_authorized`, `merged`, or `operationally_validated`.
- `ca_verified` means architectural or governance review acceptance only; it must not imply merge authority unless the review record explicitly delegates that authority.
- `merge_authorized` must precede `merged` for repository or institutional promotion changes.
- `operationally_validated` should require evidence from the validation owner, not merely a successful merge.
- Terminal closure should preserve whether the path ended through completion, cancellation, supersession, or administrative closure.
- Blocked and parked states must preserve a resumable target state or closure path so work is not lost.

## Follow-on Codex Implementation Package

A follow-on implementation package has been drafted as `collaboration/work_packages/pending/WP-0020_SERIES_work_package_state_machine_implementation.md`. It must remain blocked until Chief Architect review approves this state model and authorizes implementation.

## Chief Architect Review Questions

1. Should `ca_review_pending` be mandatory for all Class B work, or only architecture/governance-adjacent Class B work?
2. Should `closed` be reachable directly from `merged`, or should all implementation packages pass through `validation_pending` first?
3. Should `blocked` return only to its immediately prior state, or may the resolving office choose a different authorized state such as `pending` or `ca_review_pending`?
4. Should merge authority be held only by the Steward, or may Chief Architect verification explicitly delegate merge authority for predefined classes?
5. Should architecture-only packages close after `ca_verified`, or should they also require a separate validation state?

## Non-Decisions

This proposal does not implement registry storage, validation tooling, transition automation, board synchronization, or migration of existing work packages. It also does not alter Estate lifecycle states outside the proposed work-package state machine.

## Recommendation

Approve the state vocabulary and transition-authority model as the canonical work-package state machine, then authorize a limited Codex implementation package that encodes the approved states as documentation and structural validation only. Defer workflow automation until the registry model and state machine have both been used successfully on real work packages.
