# SERIES TASK WP-0125 — Establish Estate Engineering Department for CueMastery Execution

## Codex Command

Read collaboration/work_packages/pending/WP-0125_SERIES_establish_estate_engineering_department_for_queue_mastery.md and do exactly what it says.

## Mode

SERIES

## Mission

Establish the Estate Engineering Department as the institutional execution unit responsible for returning CueMastery to active development through local execution.

The Estate has been built to reduce dependence on external conversational limits and expensive additional seats. The Engineering Department must provide a disciplined internal structure for local engineering work, work-package execution, validation, review, and operational handoff while preserving existing Estate governance.

This package must define the Engineering Department using existing Estate institutional patterns and avoid creating unnecessary parallel systems.

## Background

The original purpose of the Estate is to create local execution capacity so CueMastery can be built without being bottlenecked by ChatGPT usage limits or additional paid seats.

Recent work has moved the Estate from validation/buildout toward operation:

- WP-0121 resolves or classifies the final production-readiness blockers.
- WP-0122 stands up Alfred as operational resident runtime.
- WP-0123 brings Helen online as HR/onboarding resident.
- WP-0124 has Helen hire and onboard Chief Architect #5.

WP-0125 now creates the Engineering Department so the Estate can organize and execute actual engineering work, especially CueMastery.

## Preconditions

Before work begins:

1. Sync to latest main.
2. Confirm WP-0121 is merged or final blockers are explicitly classified.
3. Confirm WP-0122 is merged and Alfred is operational.
4. Confirm WP-0123 is merged and Helen is online.
5. Confirm WP-0124 is merged or Chief Architect #5 onboarding status is explicitly known.
6. Confirm production-readiness validation runs.
7. Confirm Alfred/Helen resident-runtime path remains ready.
8. Confirm WP-9999 remains quarantined/not promoted.

If preconditions fail, stop and report exact blockers.

## Scope

In scope:

1. Inspect existing Estate organizational, personnel, service, capability, and operations artifacts.
2. Define the Engineering Department as an Estate organizational unit using existing patterns.
3. Define the department mission: local engineering execution for CueMastery and Estate-maintained systems.
4. Define department responsibilities and boundaries.
5. Define relationship to Steward, Chief Architects, Helen/HR, Alfred/runtime, Codex, validation, and Operations Center.
6. Define minimal department roles without overbuilding.
7. Create an Engineering Department charter.
8. Create an Engineering Department operating guide.
9. Create initial CueMastery execution backlog handoff artifact.
10. Define intake and work-package routing rules for engineering work.
11. Define validation and completion expectations for engineering work.
12. Add Engineering Department to existing service/capability/operations surfaces where appropriate.
13. Add validation recipe and completion receipt for WP-0125.

Out of scope:

- Building CueMastery features directly.
- Creating a large engineering bureaucracy.
- Creating unnecessary new registries if existing registries can represent the department.
- Changing Steward authority.
- Changing Chief Architect authority.
- Changing Helen/HR authority.
- Changing Alfred resident authority.
- Changing production-readiness semantics.
- Hiring a full engineering staff unless existing onboarding patterns require a placeholder role.
- Creating the Social Character Engineer role unless only documented as a future hiring need.

## Department Principles

The Engineering Department must follow these principles:

- Local execution first where practical.
- Work packages remain the unit of planned work.
- Validation is part of engineering, not an afterthought.
- Chief Architects provide architectural review and challenge.
- Helen owns hiring/onboarding flows.
- Alfred supports operational runtime/duty execution where authorized.
- The Steward retains final institutional authority.
- CueMastery is the initial primary engineering product objective.
- Avoid scope creep and unnecessary new systems.

## Required Department Artifacts

Create appropriate files under existing canonical locations. Suggested paths:

`operations/departments/engineering/engineering_department_charter.md`

`operations/departments/engineering/engineering_department_operating_guide.md`

`operations/departments/engineering/queue_mastery_execution_handoff.md`

`runtime/departments/engineering/WP-0125_engineering_department_status.json`

If those paths conflict with existing conventions, use the nearest existing canonical directory and document the choice.

## Required Charter Content

The Engineering Department charter must include:

- department name
- mission
- authority boundaries
- relationship to Steward
- relationship to Chief Architects
- relationship to Helen/HR
- relationship to Alfred/runtime
- relationship to Codex
- relationship to validation system
- CueMastery as initial primary objective
- local execution principle
- work-package discipline
- review and completion expectations

## Required Operating Guide Content

The operating guide must include:

- how engineering work is proposed
- how engineering work becomes a work package
- how Codex/local execution is used
- how validation is run
- how completion receipts are created
- how Chief Architect review is requested
- how blockers are escalated
- how CueMastery work is prioritized
- what not to do: no ad hoc hidden changes, no unvalidated implementation, no bypassing governance

## Required CueMastery Handoff Content

The CueMastery handoff must include:

- statement that CueMastery is the initial primary engineering objective
- current reason CueMastery was paused: external limits and lack of local execution capacity
- how the Estate now supports local execution
- immediate next engineering discovery steps
- first recommended CueMastery work-package candidates
- dependencies and unknowns
- how to avoid derailing Estate operations while resuming CueMastery

## Required Report Artifacts

Create:

`operations/departments/engineering/WP-0125_engineering_department_establishment_report.md`

Create machine-readable companion:

`runtime/departments/engineering/WP-0125_engineering_department_establishment_report.json`

The report must include:

- current git commit
- precondition status
- files created/updated
- department charter path
- operating guide path
- CueMastery handoff path
- role/authority boundaries
- initial work intake model
- validation commands run
- production-readiness totals
- Alfred/Helen status
- Chief Architect #5 status if available
- remaining gaps
- recommended next action

## Required Tests

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Add targeted tests if new helper behavior is introduced for department discovery, service catalog, capability registry, or operations surfaces.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0121 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0122 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0123 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0124 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0125 --json
```

If WP-0124 has not yet merged when this package is executed, document that Chief Architect #5 status is pending and do not falsely claim completion of CA5 onboarding.

## Required Outputs

Update or create as applicable:

- Engineering Department charter
- Engineering Department operating guide
- CueMastery execution handoff
- Engineering Department establishment report Markdown and JSON
- status JSON under runtime department path
- validation recipe registration for WP-0125
- validation reports/runtime JSON for WP-0125
- regenerated production-readiness and coverage artifacts
- `collaboration/work_packages/completions/WP-0125_codex_done.json`

Update existing service/capability/operations artifacts only if there is a clear existing location for the Engineering Department entry. Do not create duplicate registries.

## WP-0125 Self-Validation Recipe

Add a recipe for WP-0125 that verifies:

- Engineering Department charter exists
- Engineering Department operating guide exists
- CueMastery execution handoff exists
- WP-0125 report exists
- report JSON parses
- charter states CueMastery as initial primary objective
- operating guide states work-package and validation discipline
- handoff includes immediate CueMastery next steps
- production-readiness validation executes successfully
- Alfred/Helen status is explicitly reported
- WP-0121, WP-0122, WP-0123, and WP-0124 status is reported
- WP-0125 receipt is complete

Use cross-platform Python checks only.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0125_codex_done.json`

It must include:

- `work_package_id = WP-0125`
- `codex_status = done`
- `completed_at`
- `branch`
- `summary`
- department artifacts created
- CueMastery handoff path
- authority boundaries
- tests run
- validation commands run
- production-readiness status
- Alfred/Helen status
- Chief Architect #5 status if available
- remaining gaps
- recommended next action
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0125 is complete when the Estate has a durable Engineering Department charter, operating guide, CueMastery execution handoff, validation evidence, and completion receipt, without weakening governance or creating unnecessary bureaucracy.

## Merge Class

Class A. Escalate for governance, department authority, personnel authority, engineering authority, Chief Architect authority, or production-readiness semantic changes.
