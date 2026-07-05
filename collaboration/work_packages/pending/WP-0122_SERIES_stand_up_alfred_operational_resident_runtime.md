# SERIES TASK WP-0122 — Stand Up Alfred as Operational Resident Runtime

## Codex Command

Read collaboration/work_packages/pending/WP-0122_SERIES_stand_up_alfred_operational_resident_runtime.md and do exactly what it says.

## Mode

SERIES

## Mission

Stand up Alfred as the first operational resident runtime actor of the Estate.

This package begins the transition from validation/buildout into institutional operation. Alfred must be brought online using existing Estate runtime, mailbox, resident presence, duty, authority, audit, and Operations Center surfaces without inventing new departments or bypassing existing governance.

The goal is to prove Alfred can operate as a resident/runtime participant inside the Estate, not merely pass isolated validation commands.

## Background

WP-0119 restored Alfred/Helen resident-runtime validation readiness. WP-0120 reduced historical blockers to four. WP-0121 is expected to resolve or classify the final four blockers. WP-0122 should only proceed after WP-0121 is merged and local production-readiness verification confirms the resident runtime path remains ready.

Known Alfred identity:

- Employee ID: 7
- Resident ID: RES-000001
- Mailbox ID: 7
- Legacy/intake mailbox reference: mailbox.10100

## Preconditions

Before performing operational standing-up work:

1. Sync to latest main.
2. Confirm WP-0121 is merged.
3. Run production-readiness validation.
4. Confirm Alfred-related packages are ready, especially WP-0019, WP-0106, WP-0107, WP-0109, WP-0110, WP-0118, WP-0119.
5. Confirm WP-9999 remains quarantined/not promoted.

If preconditions fail, stop and report exact blockers. Do not force operational activation.

## Scope

In scope:

1. Inspect Alfred resident identity, mailbox, duty, presence, authority, and audit artifacts.
2. Confirm Alfred has a coherent runtime identity across personnel/resident/mailbox references.
3. Run Alfred resident presence and duty commands.
4. Ensure Alfred duty state and duty summaries are generated and readable.
5. Ensure Alfred's runtime actions are recorded in audit/runtime artifacts where existing systems support it.
6. Ensure Alfred is visible through existing Operations Center / resident card / command center surfaces.
7. Ensure Alfred can receive or inspect institutional correspondence through existing mailbox/duty mechanisms where implemented.
8. Create an Alfred operational standing-up report.
9. Add a validation recipe for WP-0122.
10. Create a WP-0122 completion receipt.

Out of scope:

- Creating a new department.
- Creating a new resident registry if existing registries can represent Alfred.
- Changing Alfred's identity values.
- Giving Alfred new authority beyond existing resident action authority boundaries.
- Bypassing Steward, Chief Architect, or governance authority.
- Implementing Helen onboarding in this package except to identify whether Alfred can initiate or assist it.
- Hiring Chief Architect #5.
- Building Queue Mastery.

## Required Operational Checks

Run or document equivalent checks:

```bash
PYTHONPATH=src python -m estate.cli.main resident-presence --resident Alfred --json
PYTHONPATH=src python -m estate.cli.main alfred-duty --json
PYTHONPATH=src python -m estate.cli.main resident-duty --resident Alfred --json
PYTHONPATH=src python -m estate.cli.main resident-authority list --resident Alfred --json
PYTHONPATH=src python -m estate.cli.main resident-authority check --resident Alfred --action summarize --json
PYTHONPATH=src python -m estate.cli.main resident-authority check --resident Alfred --action execute-work-package --json
PYTHONPATH=src python -m estate.cli.main steward-command-center --json
```

If a command is unavailable, report the exact missing command and use the closest existing artifact path without creating parallel systems.

## Required Report Artifacts

Create:

`operations/residents/alfred/WP-0122_alfred_operational_standup_report.md`

Create machine-readable companion:

`runtime/residents/alfred/WP-0122_alfred_operational_standup_report.json`

The report must include:

- current git commit
- production-readiness status before activation
- Alfred identity mapping
- mailbox mapping
- presence command results
- duty command results
- authority check results
- audit/runtime artifacts created or updated
- Operations Center / resident card visibility
- whether Alfred can assist Helen onboarding
- remaining gaps
- recommended next action

## Required Tests

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Run relevant resident runtime tests:

```bash
PYTHONPATH=src python -m pytest tests/test_alfred_duty.py tests/test_resident_presence.py tests/test_resident_cards.py tests/test_resident_authority.py
```

Add targeted tests only if implementation changes are required.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0106 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0107 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0109 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0110 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0119 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0121 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0122 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Required Outputs

Update or create as applicable:

- Alfred operational report Markdown and JSON
- any existing Alfred runtime artifacts generated by normal operation
- validation recipe registration for WP-0122
- validation reports/runtime JSON for WP-0122
- regenerated production-readiness and coverage artifacts
- `collaboration/work_packages/completions/WP-0122_codex_done.json`

## WP-0122 Self-Validation Recipe

Add a recipe for WP-0122 that verifies:

- Alfred operational report exists
- JSON companion parses
- report includes Alfred identity and mailbox mapping
- Alfred presence command succeeds
- Alfred duty command succeeds
- resident authority checks are reported
- Alfred is visible through existing resident/command center surfaces where available
- production-readiness validation executes successfully
- WP-0106, WP-0107, WP-0109, WP-0110, WP-0119, and WP-0121 remain passing
- WP-0122 receipt is complete

Use cross-platform Python checks only.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0122_codex_done.json`

It must include:

- `work_package_id = WP-0122`
- `codex_status = done`
- `completed_at`
- `branch`
- `summary`
- Alfred identity status
- mailbox status
- commands run
- tests run
- validation commands run
- operational artifacts created
- remaining gaps
- recommended next action
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0122 is complete when Alfred can be treated as stood up operationally through existing Estate runtime surfaces, or any remaining activation blocker is precisely documented with a next action.

## Merge Class

Class A. Escalate only for governance, authority, identity, or production-readiness semantic changes.
