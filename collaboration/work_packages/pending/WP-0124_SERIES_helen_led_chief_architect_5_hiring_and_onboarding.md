# SERIES TASK WP-0124 — Helen-Led Chief Architect #5 Hiring and Onboarding

## Codex Command

Read collaboration/work_packages/pending/WP-0124_SERIES_helen_led_chief_architect_5_hiring_and_onboarding.md and do exactly what it says.

## Mode

SERIES

## Mission

Have Helen perform the institutional hiring and onboarding of Chief Architect #5 through Estate artifacts.

This package must create a durable personnel identity, mailbox assignment, onboarding packet, communication-bus notice, and audit trail for Chief Architect #5. The goal is to make the new Chief Architect an institutional participant, not merely a chat persona.

Helen should perform or orchestrate the onboarding if WP-0123 confirms she is online and ready. If Helen cannot perform the action through current runtime surfaces, Codex must stop and report the missing capability rather than bypassing Helen silently.

## Background

Chief Architect #5 is intended to replace Chief Architect #3 as the second active Chief Architect while preserving historical identities. The Estate maintains two active Chief Architects for independent architectural review, peer challenge, and validation before major institutional decisions are accepted.

Known active/historical context:

- Chief Architect #1: historical foundation occupant.
- Chief Architect #2: senior active/historical occupant.
- Chief Architect #3: current active occupant being prepared for replacement.
- Chief Architect #4: current active assistant identity, Employee ID 5 / Mailbox ID 5.
- Chief Architect #5: new hire to be onboarded after Helen is online.

## Preconditions

Before work begins:

1. Confirm the checkout contains the merged prerequisite artifacts from WP-0121, WP-0122, and WP-0123.
2. If an `origin` remote is configured, sync to latest main before making changes.
3. If no `origin` remote is configured in the Codex checkout, record that as an execution-environment limitation and continue using the provided checkout state.
4. Confirm WP-0121 is merged or final-four blockers are resolved/classified.
5. Confirm WP-0122 is merged and Alfred is operationally stood up.
6. Confirm WP-0123 is merged and Helen is online as HR/onboarding resident.
7. Confirm Helen readiness report states she is ready to hire/onboard Chief Architect #5, or explicitly records the precise runtime limitation that requires a manual HR/onboarding artifact path.
8. Confirm production-readiness validation runs.
9. Confirm WP-9999 remains quarantined/not promoted.

If any substantive Estate precondition fails, stop and report exact blockers.

A missing `origin` remote in Codex is not a substantive Estate blocker by itself when the provided checkout already contains the merged prerequisite artifacts.

## Scope

In scope:

1. Determine the next available personnel identity and mailbox assignment using existing Estate standards.
2. Create or update the appropriate personnel/staff/role artifacts for Chief Architect #5.
3. Create or update mailbox artifacts for Chief Architect #5.
4. Create a Chief Architect #5 onboarding packet.
5. Include required governance, historical, and operating-document references.
6. Create an HR/onboarding action record showing Helen performed or orchestrated the hire.
7. Create a Communication Bus notice announcing the hire/onboarding where existing patterns support it.
8. Create audit/runtime artifacts showing the onboarding action.
9. Preserve prior Chief Architect historical records.
10. Do not erase or overwrite Chief Architect #3 history.
11. Add validation recipe and completion receipt for WP-0124.

Out of scope:

- Changing the Estate Constitution.
- Rewriting Chief Architect authority.
- Removing Chief Architect #3 artifacts.
- Creating the Social Character Engineer role.
- Creating the Engineering Department.
- Building Queue Mastery.
- Granting Chief Architect #5 permissions beyond established Chief Architect role boundaries.

## Required Onboarding Packet

Create a durable onboarding packet at an appropriate existing location, such as:

`onboarding/chief_architects/chief_architect_5_onboarding_packet.md`

or the closest existing canonical onboarding path.

The packet must include:

- identity assignment
- employee/personnel ID
- mailbox ID
- role title: Chief Architect #5
- relationship to prior Chief Architects
- onboarding sequence
- required documents to read
- governance principles
- validation responsibilities
- Codex/work-package operating rules
- Communication Bus usage expectations
- current production-readiness status
- current active priorities
- explicit instruction not to redesign constitutional systems without evidence

## Required Institutional Records

Create or update existing artifacts as applicable:

- personnel/staff roster entry
- mailbox assignment artifact
- onboarding packet
- HR/onboarding action record
- Communication Bus or institutional announcement record
- audit/runtime record
- validation report and runtime JSON
- WP-0124 completion receipt

Use existing directories and formats. Do not create a parallel registry if an existing one can be extended.

## Required Report Artifacts

Create:

`operations/onboarding/WP-0124_chief_architect_5_hiring_onboarding_report.md`

Create machine-readable companion:

`runtime/onboarding/WP-0124_chief_architect_5_hiring_onboarding_report.json`

The report must include:

- current git commit
- precondition status
- origin remote availability and any sync limitation
- Helen readiness status
- whether Helen performed/orchestrated the hire
- Chief Architect #5 identity assignment
- mailbox assignment
- artifacts created/updated
- onboarding packet path
- communication notice path
- audit/runtime record path
- tests run
- validation commands run
- remaining gaps
- recommended next action

## Required Tests

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Add targeted tests if new helper behavior is introduced for personnel, mailbox, onboarding, or communication-bus artifacts.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0122 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0123 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0124 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Run any existing personnel/mailbox/onboarding commands if available. If no command exists, validate by artifact presence and schema/anchor checks.

## Required Outputs

Update or create as applicable:

- Chief Architect #5 onboarding packet
- personnel/staff roster artifacts
- mailbox assignment artifacts
- HR/onboarding action record
- communication notice / bus record
- audit/runtime record
- WP-0124 report Markdown and JSON
- validation recipe registration for WP-0124
- validation reports/runtime JSON for WP-0124
- regenerated production-readiness and coverage artifacts
- `collaboration/work_packages/completions/WP-0124_codex_done.json`

## WP-0124 Self-Validation Recipe

Add a recipe for WP-0124 that verifies:

- WP-0124 report exists
- JSON companion parses
- Chief Architect #5 onboarding packet exists
- identity assignment is present
- mailbox assignment is present
- Helen involvement is explicitly reported
- communication/audit record is present or a precise existing-system limitation is reported
- production-readiness validation executes successfully
- WP-0122 and WP-0123 remain passing
- WP-0124 receipt is complete

Use cross-platform Python checks only.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0124_codex_done.json`

It must include:

- `work_package_id = WP-0124`
- `codex_status = done`
- `completed_at`
- `branch`
- `summary`
- Chief Architect #5 identity assignment
- mailbox assignment
- Helen action evidence
- artifacts created/updated
- tests run
- validation commands run
- origin remote/sync status
- remaining gaps
- recommended next action
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0124 is complete when Chief Architect #5 has a durable Estate personnel identity, mailbox, onboarding packet, institutional announcement/audit trail, and validation evidence, or a precise blocker explains why Helen cannot yet complete the hire.

## Merge Class

Class A. Escalate for governance, personnel identity, mailbox assignment, Chief Architect authority, HR authority, or merge authority changes.
