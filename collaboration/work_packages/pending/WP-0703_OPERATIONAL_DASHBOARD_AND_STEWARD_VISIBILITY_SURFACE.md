# WP-0703 — Operational Dashboard and Steward Visibility Surface

## Campaign
CAMPAIGN-0681 — Estate Operationalization

## Purpose
Provide a consolidated operational visibility surface for the Steward and authorized offices that presents campaign momentum, blockers, readiness, service health, pending decisions, and authority boundaries without becoming a parallel system of record.

## Objectives
- Present the highest-value operational signals in one coherent view.
- Preserve direct links to canonical evidence and authoritative records.
- Distinguish observation, derived state, recommendation, required decision, and authorized action.
- Support rapid identification of stalled campaigns, unhealthy services, unresolved blockers, and evidence gaps.

## Required Work
1. Define the minimum dashboard information architecture and user journeys.
2. Integrate outputs from health, momentum, blocker, readiness, office, and audit work packages.
3. Define freshness, confidence, provenance, and stale-data presentation.
4. Define role-aware visibility and redaction behavior.
5. Provide drill-through links to canonical records and evidence.
6. Define accessibility, performance, and representative operational scenario tests.

## Constraints
- Do not create a new authoritative campaign, work-package, staffing, mailbox, or service registry.
- Do not hide uncertainty, conflicting evidence, or stale signals behind simplified status colors.
- Do not expose controls unless the user and action are explicitly authorized.
- Dashboard summaries must remain traceable to source records.

## Deliverables
- Dashboard information architecture.
- Steward and office visibility views.
- Signal freshness and confidence presentation rules.
- Role-aware access and redaction behavior.
- Canonical drill-through contract.
- Representative usability and integrity tests.

## Acceptance Criteria
- The Steward can identify the Estate's highest-priority operational constraints from one surface.
- Every displayed status is traceable to canonical evidence.
- Stale, conflicting, or incomplete information is visibly distinguished.
- The surface does not become a competing system of record or unauthorized control plane.

## Dependencies
- WP-0691
- WP-0692
- WP-0693
- WP-0694
- WP-0695
- WP-0696
- WP-0697
- WP-0698
- WP-0702

## Constitutional Precedence
The dashboard is a derived visibility surface only. Canonical repository records, office systems, constitutional authority, and accepted decisions remain authoritative.
## Executable Validation Commands

Run the following commands from the repository root after implementation and
after creating this package's completion receipt:

    pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0703
    git diff --check

Run all additional affected-subsystem tests discovered during implementation.
Record every exact command, result, environment, unresolved gap, and failure
disposition in the package completion receipt.

A prose expected outcome is not a substitute for executing the commands above.
