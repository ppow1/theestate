# WP-0701 — Operational Policy and Guardrail Enforcement

## Campaign
CAMPAIGN-0681 — Estate Operationalization

## Purpose
Define and implement the policy evaluation layer that constrains operational recommendations and actions so the Estate can sustain momentum without bypassing constitutional, office, campaign, or work-package authority.

## Objectives
- Translate existing constitutional, office, campaign, and work-package constraints into machine-evaluable operational guardrails.
- Distinguish advisory recommendations from authorized actions.
- Block or route actions that exceed delegated authority.
- Produce auditable explanations for every allow, deny, defer, or escalate decision.

## Required Work
1. Inventory canonical authority and policy sources relevant to operational action.
2. Define a normalized guardrail rule model with scope, authority source, effective period, and precedence.
3. Integrate guardrail checks with the action taxonomy from WP-0690 and the momentum engine from WP-0700.
4. Define conflict, ambiguity, and stale-policy behavior.
5. Define evidence and audit records for policy evaluation outcomes.
6. Provide tests for permitted, denied, deferred, and escalated actions.

## Constraints
- Do not create new constitutional authority.
- Do not infer permission from silence or missing evidence.
- Do not convert advisory systems into autonomous approval systems.
- Existing canonical policy and authority records remain controlling.

## Deliverables
- Operational guardrail rule model.
- Authority and policy source inventory.
- Evaluation and precedence behavior.
- Integration contract for proposed actions.
- Audit and explanation records.
- Representative enforcement tests.

## Acceptance Criteria
- Every operational action proposal receives an explicit policy disposition.
- Denied or deferred actions identify the controlling authority or missing evidence.
- Ambiguous authority produces escalation rather than silent execution.
- The operational layer cannot grant itself additional authority.

## Dependencies
- WP-0689
- WP-0690
- WP-0693
- WP-0699
- WP-0700

## Constitutional Precedence
The Estate Constitution, canonical office authority, accepted campaign decisions, and active work-package constraints remain authoritative. This work package operationalizes their enforcement without modifying them.
## Executable Validation Commands

Run the following commands from the repository root after implementation and
after creating this package's completion receipt:

    pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0701
    git diff --check

Run all additional affected-subsystem tests discovered during implementation.
Record every exact command, result, environment, unresolved gap, and failure
disposition in the package completion receipt.

A prose expected outcome is not a substitute for executing the commands above.
