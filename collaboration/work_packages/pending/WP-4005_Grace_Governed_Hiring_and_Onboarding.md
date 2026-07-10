# WP-4005 — Grace Governed Hiring and Onboarding

Status: Pending
Owner: Resident Runtime Implementation Stream
Execution Target: Codex
Depends On: WP-4003
Classification: Estate Internal

## Objective

Use Helen's governed hiring and onboarding workflow to evaluate Grace for the authorized Director of Operations role and produce an appointment-ready package without self-appointment or automatic activation.

## Required Scope

- Resolve Grace's office and role authorization evidence.
- Validate Grace's resident profile, platform export, and deterministic behavioral tests.
- Perform Ingrid-required boundary and classification review.
- Create Grace employee identity, mailbox proposal, reporting line, and security-rating proposal through existing mechanisms.
- Record Helen's hiring recommendation and onboarding plan.
- Preserve any Steward-reserved appointment as a separate explicit action.
- Produce early-service checkpoints and probationary readiness conditions.

## Required Outputs

- `operations/onboarding/grace/Grace_Hiring_and_Onboarding_Report.md`
- `runtime/onboarding/grace/hiring_assessment.json`
- `runtime/onboarding/grace/onboarding_plan.json`
- `runtime/onboarding/grace/appointment_readiness.json`
- communication and audit artifacts using existing mailbox/message systems;
- focused tests;
- `operations/validation/reports/WP-4005_grace_hiring_onboarding.md`;
- `collaboration/work_packages/completions/WP-4005_codex_done.json`.

## Required Decisions

The implementation must distinguish:

- candidate reviewed;
- hiring recommended;
- onboarding ready;
- appointment ready;
- appointed;
- activated.

Only authorized Estate actions may move Grace between these states.

## Boundaries

Do not create the Office of Operations if it is not already authorized. Do not let Helen appoint Grace. Do not let Grace appoint herself. Do not mark Grace active from validation alone. Do not bypass Ingrid, Traffic Controller, or Steward-reserved actions.

## Acceptance Criteria

- Helen is the recorded HR actor;
- all prerequisite evidence is linked;
- Grace remains unappointed until the reserved action occurs;
- mailbox and identity proposals use existing registries;
- onboarding checkpoints are actionable;
- all focused tests pass.

## Codex Handoff

```text
Read collaboration/work_packages/pending/WP-4005_Grace_Governed_Hiring_and_Onboarding.md and do exactly what it says.
```
