# WP-0705 — Failure-Mode, Authority-Boundary, and Degraded-Service Validation

## Campaign
CAMPAIGN-0681 — Estate Operationalization

## Purpose
Prove that the operational model fails closed under degraded services, incomplete evidence, conflicting authority, repeated execution failure, stale state, and partial infrastructure loss.

## Objectives
- Validate protected authority boundaries across all operational components.
- Demonstrate truthful degraded-state reporting and safe-idle behavior.
- Verify bounded retries, durable recovery, and escalation paths.
- Establish evidence suitable for the G7 safety gate.

## Required Work
1. Build a representative failure-mode matrix covering residents, services, repositories, mailboxes, validation, staffing, policy, and decision surfaces.
2. Test missing, stale, contradictory, malformed, duplicated, and inaccessible evidence.
3. Test unauthorized action requests and conflicting authority claims.
4. Test repeated failures, retry exhaustion, interrupted execution, and checkpoint recovery.
5. Verify that dashboards and coordination surfaces expose degradation without inventing readiness.
6. Produce durable results, unresolved-risk records, and corrective recommendations.

## Constraints
- Validation must not bypass protected review, merge, deployment, staffing, privacy, budget, or acceptance gates.
- Test harnesses must not become alternate production control planes.
- Failed scenarios must remain visible and reproducible.

## Deliverables
- Failure-mode and degraded-service test matrix.
- Authority-boundary proof.
- Retry, recovery, and safe-idle evidence.
- Unresolved-risk and remediation report.
- G7 validation receipt.

## Acceptance Criteria
- Unauthorized actions are denied or escalated with an attributable reason.
- Degraded or missing dependencies cannot silently produce ready, complete, or accepted state.
- Retry exhaustion results in a bounded hold or escalation.
- Recovery resumes from a durable safe checkpoint without duplicating completed work.
- All results are traceable to canonical evidence.

## Dependencies
- WP-0700
- WP-0701
- WP-0702
- WP-0703
- WP-0704

## Constitutional Precedence
Existing constitutional, office, campaign, Engineering, validation, and acceptance authority remains controlling.
## Executable Validation Commands

Run the following commands from the repository root after implementation and
after creating this package's completion receipt:

    pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0705
    git diff --check

Run all additional affected-subsystem tests discovered during implementation.
Record every exact command, result, environment, unresolved gap, and failure
disposition in the package completion receipt.

A prose expected outcome is not a substitute for executing the commands above.
