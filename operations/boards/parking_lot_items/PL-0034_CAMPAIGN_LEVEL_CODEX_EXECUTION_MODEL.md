# PL-0034 — Campaign-Level Codex Execution Model

Status: Captured
Priority: High
Category: Engineering Campaign Execution / Codex Workflow
Originator: Pat / Steward
Date Captured: 2026-07-16
Target Milestone: After single-work-package Codex cadence is proven reliable

## Idea

Investigate and design a campaign-level Codex execution model in which one approved campaign is executed on one campaign branch, with one commit or clearly bounded commit group per included work package, and one campaign pull request for integrated review.

The intended operating pattern is:

```text
one campaign
  -> one campaign branch
  -> multiple work-package commits
  -> campaign integration gates
  -> one campaign pull request
  -> one review and merge decision
  -> one protected campaign acceptance
```

This model should preserve each work package as the atomic engineering unit while making the campaign the unit of coordinated execution, review, integration, and handoff.

## Potential Benefits

- fewer GitHub permission prompts and fewer manual handoffs;
- less Steward interruption between work packages;
- one integrated review surface for the whole campaign;
- cleaner campaign-level dependency and integration evidence;
- easier validation of cross-package contracts before merge;
- preserved work-package history through separate commits and completion receipts;
- better alignment with the Estate principle that campaigns are the unit of coordinated implementation.

## Risks Requiring Investigation

- one failed work package could complicate the entire campaign branch;
- a large campaign PR may become difficult to review;
- parallel Codex or local-worker execution may require controlled sub-branches;
- integration gates must still stop unauthorized continuation;
- rollback and partial acceptance rules must be explicit;
- a campaign branch must not become a hidden second scheduler, queue, or source of truth;
- Codex must not merge, bypass protected acceptance, or silently continue past authority gates.

## Why It Is Parked

The Estate is currently proving the safer operating rhythm of one work package, one branch, one pull request, and a mandatory stop for human review. The campaign-level model is promising, but promoting it immediately would change the execution pattern while the current CAMPAIGN-0670 run is active and before enough evidence exists to design reliable failure, review, and rollback behavior.

## Promotion Condition

Promote this idea after:

1. Several work packages have completed successfully under the single-package stop-and-review command.
2. The Estate has evidence on Codex compliance with stop, no-merge, and no-next-package instructions.
3. Campaign integration gates and acceptance boundaries are proven in practice.
4. Branch, PR, validation, rollback, partial-failure, and continuity behavior can be specified without guessing.
5. The Steward intentionally authorizes an architectural investigation or implementation campaign.

## Explicit Non-Action

Do not change the current CAMPAIGN-0670 Codex cadence, combine active work packages into one PR, or instruct Codex to continue through multiple packages merely because this idea has been captured. Continue using the approved single-work-package command until this item is intentionally promoted.

## Related Evidence

- `collaboration/campaigns/CAMPAIGN_0670_ENGINEERING_DEPARTMENT_OPERATIONALIZATION.md`
- Current approved cadence: one work package, one branch, one pull request, mandatory stop for review.
- Future concept discussed with the Steward: one campaign branch, multiple bounded work-package commits, and one campaign pull request.
- Canonical Parking Lot process: `AI_COMMUNICATION_HINTS.md`.
