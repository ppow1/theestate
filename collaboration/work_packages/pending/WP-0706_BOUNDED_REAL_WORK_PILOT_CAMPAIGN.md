# WP-0706 — Bounded Real-Work Pilot Campaign

## Campaign
CAMPAIGN-0681 — Estate Operationalization

## Purpose
Run one real but bounded institutional workflow through the completed operational model to prove end-to-end coordination, truthful state, recovery, protected escalation, and evidence-backed Steward visibility.

## Objectives
- Exercise the operational model across multiple existing Estate capabilities.
- Prove dependency, readiness, health, staffing, validation, and authority evaluation.
- Demonstrate one interruption and deterministic recovery.
- Demonstrate one protected decision that is escalated and not bypassed.

## Required Work
1. Select a bounded real-work pilot with clear owner, scope, risk, and rollback conditions.
2. Record the pilot's canonical starting state and launch authorization.
3. Exercise Grace coordination, Helen staffing/capability requests, Alfred communication routing, and Engineering execution only through existing lanes.
4. Introduce or capture one controlled interruption or recoverable failure.
5. Escalate one protected decision to the proper authority.
6. Capture checkpoints, audit events, dashboard state, evidence, and final pilot outcome.
7. Produce a pilot completion receipt and unresolved-blocker report.

## Constraints
- The pilot must not automatically merge, deploy, accept, spend, staff, disclose protected information, or close the campaign.
- The pilot must be small enough to stop safely and restore deterministically.
- No office or automation may acquire authority through participation in the pilot.

## Deliverables
- Pilot selection and authorization record.
- Starting-state and readiness evidence.
- Cross-office operational receipts.
- Interruption and recovery evidence.
- Protected escalation evidence.
- Pilot completion receipt and lessons learned.

## Acceptance Criteria
- The pilot advances through canonical mechanisms rather than a parallel workflow.
- Grace, Helen, Alfred, Engineering, residents, and services participate only within accepted authority.
- One interruption is recovered from a durable checkpoint without duplicate work.
- One protected decision stops progress until handled by the proper authority.
- Steward visibility remains concise, current, and evidence-backed.
- No automatic merge, deployment, or institutional acceptance occurs.

## Dependencies
- WP-0705

## Constitutional Precedence
The pilot is evidence of operational behavior, not authority to modify constitutional or office boundaries.
## Executable Validation Commands

Run the following commands from the repository root after implementation and
after creating this package's completion receipt:

    pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0706
    git diff --check

Run all additional affected-subsystem tests discovered during implementation.
Record every exact command, result, environment, unresolved gap, and failure
disposition in the package completion receipt.

A prose expected outcome is not a substitute for executing the commands above.
