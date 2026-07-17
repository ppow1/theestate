# WP-0695 — Helen Staffing and Capability Request Integration

Status: Pending  
Priority: High  
Owner: Chief Architect  
Execution lane: Codex  
Primary campaign: CAMPAIGN-0681 — Estate Operationalization  
Depends on: WP-0690, WP-0693  
Integration gate: G3 — Office Integration

## Objective

Integrate campaign staffing and capability needs with Helen's existing authority and mechanisms so operational blockers can become explicit, evidence-backed staffing or capability requests without granting Helen engineering priority, architectural, campaign-acceptance, or Steward authority.

## Required Outcomes

The implementation shall:

1. translate qualifying blocker classifications into structured staffing or capability requests;
2. identify required role, capability, urgency, duration, constraints, and evidence;
3. route requests through Helen's canonical lane rather than a new queue;
4. preserve requester, campaign, package, and authority context;
5. distinguish staffing need, provider capability gap, environment gap, and protected policy decision;
6. record disposition, partial fulfillment, refusal, deferral, and unresolved need truthfully;
7. return staffing evidence to the operational state without treating a request as fulfillment;
8. fail closed when role ownership, authority, privacy, budget, or provider suitability is unresolved.

## Scope

- request schema and adapter;
- canonical routing to Helen;
- staffing and capability evidence correlation;
- response and disposition ingestion;
- partial-fulfillment and expiry semantics;
- tests for authority and evidence boundaries.

## Non-Goals

This package shall not:

- permit Helen to set engineering priority, alter architecture, accept deliverables, or bypass the Steward;
- treat model availability as staffing acceptance;
- auto-assign a person or provider where canonical approval is required;
- duplicate personnel, provider, mailbox, or campaign registries;
- conceal budget, privacy, environment, or readiness constraints.

## Acceptance Criteria

WP-0695 is complete when a real campaign need can be converted into a canonical staffing or capability request, resolved or declined through Helen's existing lane, and reflected back into operational state with truthful evidence and no authority transfer.

## Required Evidence

- implemented request and response integration;
- examples for fulfilled, partially fulfilled, refused, expired, and protected requests;
- authority-boundary tests;
- evidence correlation report;
- completion receipt suitable for CAMPAIGN-0681 G3 review.
## Executable Validation Commands

Run the following commands from the repository root after implementation and
after creating this package's completion receipt:

    pwsh -NoProfile -File scripts/validation/Validate-Campaign0681Package.ps1 -PackageId WP-0695
    git diff --check

Run all additional affected-subsystem tests discovered during implementation.
Record every exact command, result, environment, unresolved gap, and failure
disposition in the package completion receipt.

A prose expected outcome is not a substitute for executing the commands above.
