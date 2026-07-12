# WP-4033 — Grace Steward Appointment and Lifecycle Activation

Status: Pending
Workstream Mode: SERIES
Owner: Character Architecture / Resident Lifecycle
Execution Target: Codex
Classification: Estate Internal
Priority: Immediate

## Objective

Record the Steward's explicit appointment of Grace as Director of Operations, complete the governed lifecycle transition from appointment-ready candidate to appointed/onboarding status, and prepare Grace for live activation without bypassing Helen, Ingrid, Traffic Controller, mailbox, registry, or resident-runtime controls.

## Authoritative Steward Decision

The Steward has explicitly decided to hire and appoint Grace as Director of Operations of the Estate.

This work package is the formal implementation vehicle for that decision.

## Current Evidence

Use and reconcile the existing sources rather than creating parallel records:

- `runtime/onboarding/grace/appointment_readiness.json`
- `runtime/onboarding/grace/hiring_assessment.json`
- `runtime/onboarding/grace/onboarding_plan.json`
- `docs/residents/grace/Grace_Resident_Profile_v0_1.md`
- `docs/residents/grace/Grace_Resident_Validation_v0_1.md`
- `docs/residents/grace/platform-exports/textgen-4_9-grace-v0_1.yaml`
- `docs/residents/helen/Helen_Hiring_Onboarding_Workflow_v0_1.md`
- `data/registry/personnel.json`
- `data/registry/mailboxes.json`
- existing resident lifecycle implementation and schemas

Grace is already hiring-recommended, onboarding-ready, and appointment-ready. Employee ID 12 and mailbox ID 12 are reserved in proposed form. Do not allocate replacements.

## Required Work

1. Create a durable Steward appointment decision artifact for Grace.
2. Record the exact appointment:
   - Resident: Grace
   - Role: Director of Operations
   - Office: Office of Operations
   - Appointing authority: Steward
   - Employee ID: 12
   - Mailbox ID: 12
3. Update Grace's appointment-readiness state so it truthfully reflects the recorded appointment.
4. Transition the existing personnel and mailbox records from proposed appointment pending to the correct governed onboarding or appointed state.
5. Use the installed resident lifecycle system to record the lifecycle transition and provenance.
6. Preserve the distinction between:
   - appointed;
   - onboarding;
   - activated for live service;
   - accepted for full operational service.
7. Do not mark Grace live or active unless all activation prerequisites are actually completed in this package.
8. Confirm and preserve the following boundaries:
   - Helen owns onboarding execution and readiness evidence.
   - Ingrid review remains required for elevated or cross-office access.
   - Traffic Controller movement constraints remain binding.
   - Grace may not self-appoint, self-activate, or self-expand authority.
   - appointment does not itself authorize provider execution, unrestricted access, constitutional change, or institutional acceptance.
9. Preserve the Estate Commissioning Tradition already added to Grace's onboarding plan as voluntary culture after appointment and activation; it is not a hiring condition or authority gate.
10. Produce a clear next-action artifact identifying everything still required before `estate/grace` may be exposed through the resident gateway and Open WebUI.

## Required Outputs

At minimum:

- durable Steward appointment decision artifact;
- updated `runtime/onboarding/grace/appointment_readiness.json`;
- reconciled Grace personnel record using employee ID 12;
- reconciled Grace mailbox record using mailbox ID 12;
- resident lifecycle transition record with evidence and authority provenance;
- human-readable appointment and onboarding status report;
- deterministic tests covering appointment authority, state transitions, fixed IDs, no premature activation, and idempotent rerun behavior;
- validation report;
- completion receipt at `collaboration/work_packages/completions/WP-4033_codex_done.json`.

## Acceptance Criteria

WP-4033 is complete only when:

1. The Steward appointment is durably recorded and source-linked.
2. Grace is no longer represented as merely awaiting appointment.
3. Employee ID 12 and mailbox ID 12 remain stable and are reconciled rather than duplicated.
4. Lifecycle history clearly identifies the Steward as appointment authority.
5. Grace is not falsely represented as live if gateway/runtime activation has not occurred.
6. Helen, Ingrid, Traffic Controller, and Steward authority boundaries remain intact.
7. A deterministic next action identifies the package needed to make Grace conversationally available as `estate/grace`.
8. Focused tests pass.

## Prohibited Outcomes

Do not:

- create a second personnel, mailbox, resident, lifecycle, appointment, or authority registry;
- issue a new employee or mailbox ID;
- appoint Grace through Helen or any authority other than the Steward;
- mark Grace fully active merely because appointment is recorded;
- add `estate/grace` to the gateway in this package unless every required runtime and behavioral activation prerequisite is genuinely completed and validated;
- rewrite Grace into a generic assistant or weaken her Director of Operations role;
- make ceremonial behavior a condition of employment, authority, access, or acceptance.

## Validation

Run focused deterministic tests for:

- explicit Steward authority;
- fixed employee and mailbox IDs;
- appointment-state reconciliation;
- lifecycle provenance;
- no self-appointment;
- no premature live activation;
- idempotent rerun behavior;
- preservation of onboarding and security gates.

## Codex Handoff

Read `collaboration/work_packages/pending/WP-4033_Grace_Steward_Appointment_and_Lifecycle_Activation.md` and do exactly what it says.
