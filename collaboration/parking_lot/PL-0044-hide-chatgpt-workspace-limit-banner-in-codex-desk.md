# PL-0044 — Hide ChatGPT Workspace Limit Banner in Codex Desk

Status: Captured
Priority: Low
Category: Operator UX / Codex Desk / Browser Presentation
Originator: Pat / Steward
Date Captured: 2026-08-11
Target Milestone: After current Grace / parallelism work is stabilized

## Idea

Provide a narrow presentation-layer way to hide the persistent ChatGPT workspace-limit banner in the dedicated Codex Desk interactive Chrome app windows when auto-reload is intentionally disabled.

Observed banner text includes:

`A workspace member hit a limit`

and a `Turn on auto-reload` control.

The problem is not the limit itself. Different C1/C2/C3 seats have separate usage/fuel buckets, and exhaustion of one seat is expected operational state. The problem is that the banner permanently consumes useful vertical screen real estate in the bottom Codex Desk app surface even when the Steward has no intention of enabling auto-reload.

## Desired Behavior

When promoted, determine whether ChatGPT provides a legitimate supported dismiss/persistence mechanism first.

If no supported dismiss mechanism exists, consider a very narrow cosmetic suppression mechanism that applies only to the dedicated Codex Desk interactive Chrome app surfaces.

Requirements:

- hide only the specific workspace-limit / auto-reload banner;
- do not enable auto-reload;
- do not change billing, workspace, quota, or credit behavior;
- do not hide broader usage/fuel evidence elsewhere in the Estate;
- do not alter C1/C2/C3 seat identity or Chrome profile isolation;
- fail open if ChatGPT DOM structure changes or the target cannot be identified confidently;
- avoid a broad ad blocker / generic banner suppression mechanism;
- keep implementation local to the existing Codex Desk/browser presentation boundary if possible.

## Rationale

The bottom Codex Desk row is intentionally optimized for dense operator visibility. Persistent non-actionable UI consumes a meaningful portion of the available 50% monitor-height allocation.

Pat does not intend to enable automatic credit reload for this condition, so the banner provides no useful recurring action after the condition is understood.

## Explicit Non-Action

This item is parked.

Do not interrupt current Grace, parallelism, Codex routing, or Codex Desk stabilization work to implement it.

Do not broaden this into general ChatGPT DOM customization, browser extension development, or workspace billing automation.

Do not change current C1/C2/C3 quota/fuel policy.

## Promotion Condition

Promote only when:

1. Grace / parallel execution work is stable enough to return to Codex Desk polish;
2. the current ChatGPT UI still presents the banner without a supported dismiss option;
3. a bounded cosmetic suppression can be implemented without affecting authentication, billing, quota, or unrelated UI;
4. the Steward intentionally authorizes the presentation change.

## Related

- Codex Desk 3x3 workspace
- C1/C2/C3 independent ChatGPT/Codex seats
- Codex seat fuel telemetry
- Interactive Chrome app-mode seat surfaces
