# PL-OPS-0001 — Define Work Package Lifecycle & Pending Queue Cleanup

Status: Parking Lot
Priority: Medium
Type: Architecture Debt
Owner: Queue Orchestrator / Alfred
Created: 2026-07-07

## Problem

The current work-package pending area is at risk of becoming overloaded. It appears to function both as:

- the intake queue for newly authored work packages; and
- a historical holding area for work packages that may already have been assigned, executed, or otherwise superseded.

This makes `pending` less useful as an operational signal. If completed or assigned work remains in `pending`, the filesystem alone cannot answer whether an item is actually waiting for dispatch.

## Why this matters

The Estate is moving toward Queue Orchestrator, Operator Deck, and local Codex dispatch automation. Those systems will need a reliable work-package lifecycle so they can determine:

- what is newly authored;
- what is ready for Steward approval;
- what has been assigned to C1, C2, C3, or another worker;
- what is in progress;
- what is waiting for review;
- what is completed, cancelled, superseded, or archived.

If `pending` remains cumulative, the Queue Orchestrator will need extra metadata or manual interpretation to avoid re-dispatching stale work.

## Questions to resolve later

- Should work packages be moved or copied when assigned?
- Should `pending` contain only undispatched work?
- Should Codex workers receive per-worker assigned lanes such as `assigned/C1`, `assigned/C2`, and `assigned/C3`?
- Which component owns lifecycle transitions: Steward, Queue Orchestrator, local automation, or a combination?
- How should completed, cancelled, blocked, superseded, and abandoned work be represented?
- What state is authoritative: directory location, metadata inside the file, or both?
- How should old pending items be cleaned up without losing historical record?

## Candidate lifecycle

```text
Draft
  -> Pending
  -> Approved
  -> Assigned
  -> In Progress
  -> Review
  -> Completed
  -> Archived
```

Optional terminal or branch states:

```text
Blocked
Cancelled
Superseded
Rejected
Abandoned
```

## Candidate directory model

```text
collaboration/work_packages/draft/
collaboration/work_packages/pending/
collaboration/work_packages/approved/
collaboration/work_packages/assigned/C1/
collaboration/work_packages/assigned/C2/
collaboration/work_packages/assigned/C3/
collaboration/work_packages/in_progress/C1/
collaboration/work_packages/in_progress/C2/
collaboration/work_packages/in_progress/C3/
collaboration/work_packages/review/
collaboration/work_packages/completed/
collaboration/work_packages/archive/
```

This model is exploratory only. It should not be treated as approved architecture until reviewed in context with Queue Orchestrator and Codex dispatch automation.

## Deferral reason

This is real architecture debt, but it is not the highest priority right now. The immediate priority remains stabilizing the Operator Console, Chrome profiles, Operator Deck, and near-term C1/C2/C3 workflow. This item is captured so it does not get lost while that work continues.
