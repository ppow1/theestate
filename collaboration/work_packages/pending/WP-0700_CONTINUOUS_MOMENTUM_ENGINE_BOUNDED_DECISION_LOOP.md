# WP-0700 — Continuous Momentum Engine (Bounded Decision Loop)

## Campaign
CAMPAIGN-0681 — Estate Operationalization

## Purpose
Define a bounded decision loop that continuously evaluates operational evidence, identifies the next permitted action, and advances campaign momentum without creating autonomous authority or bypassing canonical dispatch, validation, acceptance, and escalation processes.

## Objectives
- Convert observable operational state into explicit next-action recommendations.
- Distinguish actions that may be performed automatically from actions that require office, campaign, Engineering, or Steward authority.
- Prevent inactivity caused by missing coordination while also preventing unauthorized self-direction.
- Make every recommendation and action traceable to current evidence, policy, and authority.

## Required Work
1. Define the decision-loop stages: observe, reconcile, classify, propose, authorize, act, verify, and record.
2. Define input contracts from health, momentum, blocker, office-integration, Engineering, and readiness projections.
3. Define deterministic priority rules for actionable work, blocked work, degraded services, stale evidence, and unresolved authority requirements.
4. Define the boundary between recommendation, preauthorized action, delegated action, and prohibited action.
5. Define loop cadence, event-driven wakeups, deduplication, cooldowns, and safe-idle behavior.
6. Integrate pause, resume, retry, and recovery controls from WP-0699.
7. Define evidence capture for each proposed, approved, attempted, completed, rejected, or deferred action.
8. Define simulation and dry-run modes for validating decision behavior before live operation.

## Constraints
- The engine is not a new office, sovereign actor, dispatcher, reviewer, or acceptance authority.
- It may not invent work, alter constitutional authority, or reinterpret settled decisions.
- Automatic actions must be explicitly preauthorized, bounded, idempotent, and auditable.
- Uncertainty, conflicting evidence, or missing authority must result in escalation or safe idle, not assumption.
- Canonical records must be updated only through existing authorized mechanisms.

## Deliverables
- Bounded decision-loop architecture.
- Input and output contracts.
- Action-permission and authority matrix.
- Priority, deduplication, cooldown, and safe-idle rules.
- Recommendation and action evidence schema.
- Simulation and dry-run harness design.
- Representative tests for progress, blockage, degradation, stale evidence, conflicting authority, and repeated failure.

## Acceptance Criteria
- The loop can identify and recommend a valid next action from representative campaign states.
- No action executes without explicit authority classification and required authorization.
- Duplicate events and repeated evaluations do not produce duplicate work.
- Missing or contradictory evidence produces a visible hold or escalation.
- Every recommendation and action is reproducible from recorded inputs and policy.
- The engine increases operational continuity without replacing any canonical authority.

## Dependencies
- WP-0689
- WP-0690
- WP-0691
- WP-0692
- WP-0693
- WP-0694
- WP-0695
- WP-0696
- WP-0697
- WP-0698
- WP-0699

## Constitutional Precedence
The Estate Constitution, Steward authority, office charters, campaign governance, Engineering governance, and accepted institutional records remain authoritative. The Continuous Momentum Engine may coordinate only within explicitly granted operational bounds.
## Executable Validation Commands

Run the following commands from the repository root after implementation and
after creating this package's completion receipt:

    pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0700
    git diff --check

Run all additional affected-subsystem tests discovered during implementation.
Record every exact command, result, environment, unresolved gap, and failure
disposition in the package completion receipt.

A prose expected outcome is not a substitute for executing the commands above.
