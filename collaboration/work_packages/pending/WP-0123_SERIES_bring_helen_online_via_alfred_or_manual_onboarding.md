# SERIES TASK WP-0123 — Bring Helen Online Through Alfred or Manual HR Onboarding

## Codex Command

Read collaboration/work_packages/pending/WP-0123_SERIES_bring_helen_online_via_alfred_or_manual_onboarding.md and do exactly what it says.

## Mode

SERIES

## Mission

Bring Helen online as the Estate's Human Resources / onboarding resident so she can become the institutional owner of future hiring and onboarding flows.

Preferred path: Alfred assists or performs Helen's onboarding through existing Estate runtime mechanisms.

Fallback path: If Alfred cannot perform the onboarding with current authority/runtime surfaces, perform a documented manual onboarding for Helen and record exactly why manual intervention was required.

Helen must be stood up through Estate artifacts, not just chat statements.

## Background

WP-0122 stands up Alfred as the first operational resident runtime actor. WP-0123 follows Alfred's standup and uses the existing resident runtime, mailbox, HR/onboarding, presence, duty, authority, and audit systems to bring Helen online.

Known Helen identity:

- Mailbox ID: 6
- Resident ID: RES-000003
- Role: Human Resources / onboarding

Helen is expected to become the normal hiring/onboarding authority for future personnel and residents after this package, including Chief Architect #5 and the Social Character Engineer.

## Preconditions

Before work begins:

1. Sync to latest main.
2. Confirm WP-0121 is merged and production-readiness is regenerated.
3. Confirm WP-0122 is merged and Alfred operational standup validates.
4. Confirm Alfred resident runtime checks pass.
5. Confirm Helen-related packages are ready, especially WP-0020, WP-0080, WP-0106, WP-0108, WP-0109, WP-0110, WP-0119.
6. Confirm WP-9999 remains quarantined/not promoted.

If preconditions fail, stop and report exact blockers.

## Scope

In scope:

1. Inspect Helen's identity, mailbox, resident presence, HR/onboarding, duty, authority, and audit artifacts.
2. Determine whether Alfred can initiate or assist Helen onboarding with current authority boundaries.
3. If Alfred can perform the onboarding, route the onboarding through Alfred and record the institutional evidence.
4. If Alfred cannot perform the onboarding, complete Helen's onboarding manually and document the reason.
5. Ensure Helen has coherent identity across mailbox/resident/personnel/role references.
6. Ensure Helen presence and duty commands run successfully.
7. Ensure Helen's HR/onboarding capability is visible through existing Estate surfaces.
8. Ensure any onboarding action is recorded in existing audit/runtime artifacts where supported.
9. Create Helen online report in Markdown and JSON.
10. Add WP-0123 validation recipe and completion receipt.

Out of scope:

- Hiring Chief Architect #5.
- Hiring Social Character Engineer.
- Creating an Engineering Department.
- Granting Helen authority beyond existing HR/onboarding and resident action boundaries.
- Creating duplicate identity registries.
- Bypassing governance or Chief Architect authority.
- Redesigning Alfred or Helen personalities.

## Required Operational Checks

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main resident-presence --resident Helen --json
PYTHONPATH=src python -m estate.cli.main helen-duty --json
PYTHONPATH=src python -m estate.cli.main resident-duty --resident Helen --json
PYTHONPATH=src python -m estate.cli.main resident-authority list --resident Helen --json
PYTHONPATH=src python -m estate.cli.main resident-authority check --resident Helen --action summarize --json
PYTHONPATH=src python -m estate.cli.main resident-authority check --resident Helen --action modify-personnel --json
PYTHONPATH=src python -m estate.cli.main steward-command-center --json
```

Also inspect Alfred readiness:

```bash
PYTHONPATH=src python -m estate.cli.main resident-presence --resident Alfred --json
PYTHONPATH=src python -m estate.cli.main alfred-duty --json
PYTHONPATH=src python -m estate.cli.main resident-duty --resident Alfred --json
```

## Required Report Artifacts

Create:

`operations/residents/helen/WP-0123_helen_online_onboarding_report.md`

Create machine-readable companion:

`runtime/residents/helen/WP-0123_helen_online_onboarding_report.json`

The report must include:

- current git commit
- precondition status
- whether Alfred performed/assisted onboarding
- if manual onboarding was used, why it was required
- Helen identity mapping
- mailbox mapping
- HR/onboarding role mapping
- presence results
- duty results
- authority results
- audit/runtime artifacts created or updated
- Operations Center / command center visibility
- whether Helen is ready to hire/onboard Chief Architect #5
- remaining gaps
- recommended next action

## Required Tests

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m pytest tests/test_helen_duty.py tests/test_resident_presence.py tests/test_resident_cards.py tests/test_resident_authority.py
```

Add targeted tests only if implementation changes are required.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0020 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0080 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0108 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0110 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0119 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0122 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0123 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

## Required Outputs

Update or create as applicable:

- Helen online onboarding report Markdown and JSON
- existing Helen runtime artifacts generated by normal operation
- validation recipe registration for WP-0123
- validation reports/runtime JSON for WP-0123
- regenerated production-readiness and coverage artifacts
- `collaboration/work_packages/completions/WP-0123_codex_done.json`

## WP-0123 Self-Validation Recipe

Add a recipe for WP-0123 that verifies:

- Helen online report exists
- JSON companion parses
- report identifies Alfred-assisted or manual onboarding path
- Helen identity and mailbox mapping are present
- Helen presence command succeeds
- Helen duty command succeeds
- Helen authority checks are reported
- report states whether Helen is ready for CA5 onboarding
- production-readiness validation executes successfully
- WP-0020, WP-0080, WP-0108, WP-0110, WP-0119, and WP-0122 remain passing
- WP-0123 receipt is complete

Use cross-platform Python checks only.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0123_codex_done.json`

It must include:

- `work_package_id = WP-0123`
- `codex_status = done`
- `completed_at`
- `branch`
- `summary`
- onboarding path used
- Helen identity status
- mailbox status
- HR/onboarding readiness status
- commands run
- tests run
- validation commands run
- operational artifacts created
- remaining gaps
- recommended next action
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0123 is complete when Helen is institutionally online through existing Estate artifacts and ready to perform future hiring/onboarding workflows, or a precise blocker explains why not.

## Merge Class

Class A. Escalate only for governance, HR authority, personnel identity, resident authority, or production-readiness semantic changes.
