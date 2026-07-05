# SERIES TASK WP-0118 — Repair Resident Runtime Pytest Validation Failures

## Codex Command

Read collaboration/work_packages/pending/WP-0118_SERIES_repair_resident_runtime_pytest_validation_failures.md and do exactly what it says.

## Mode

SERIES

## Mission

Repair the remaining local pytest validation failures across the Resident Runtime readiness path after WP-0117 merged.

WP-0117 fixed one issue: the WP-0106 and WP-0107 recipe pytest commands no longer depend on ambient `PYTHONPATH`. Local post-merge verification confirmed the repository was on latest main at merge commit `e0a5df8`, but validations still failed. The failures now affect the resident runtime path more broadly:

- WP-0106
- WP-0107
- WP-0108
- WP-0109
- WP-0110
- WP-0117

CLI smoke checks are passing. Pytest-based validation commands are failing. This package must inspect the actual failure captures, identify the real cause, repair it narrowly, and restore the resident runtime path to production-ready status without weakening validation semantics.

## Background

Local verification after PR #122 / WP-0117 showed latest main was being used:

- local HEAD: `e0a5df8`
- merge commit: `e0a5df8b53d4c052247c970365cbce1597f71afd`
- command used: `git fetch origin main` then `git reset --hard origin/main`

Observed failures:

### WP-0106

CLI checks passed:

- `python -m estate.cli.main resident-presence --json`
- `python -m estate.cli.main resident-presence --resident Alfred --json`

Pytest command failed:

```bash
python -c "import sys; sys.path.insert(0, 'src'); import pytest; raise SystemExit(pytest.main(['tests/test_resident_presence.py', 'tests/test_resident_cards.py', 'tests/test_steward_command_center.py']))"
```

### WP-0107

CLI checks passed:

- `python -m estate.cli.main alfred-duty --json`
- `python -m estate.cli.main resident-duty --resident Alfred --json`
- `python -m estate.cli.main resident-presence --resident Alfred --json`

Pytest command failed:

```bash
python -c "import sys; sys.path.insert(0, 'src'); import pytest; raise SystemExit(pytest.main(['tests/test_alfred_duty.py', 'tests/test_resident_presence.py', 'tests/test_resident_cards.py']))"
```

### WP-0108

CLI checks passed:

- `python -m estate.cli.main helen-duty --json`
- `python -m estate.cli.main resident-duty --resident Helen --json`
- `python -m estate.cli.main resident-presence --resident Helen --json`

Pytest command failed:

```bash
python -m pytest tests/test_helen_duty.py tests/test_resident_presence.py tests/test_resident_cards.py
```

### WP-0109

CLI check passed:

- `python -m estate.cli.main resident-conversation --help`

Pytest command failed:

```bash
python -m pytest tests/test_resident_conversation_sessions.py tests/test_resident_conversations.py
```

### WP-0110

Resident authority CLI checks passed. Pytest command failed:

```bash
python -m pytest tests/test_resident_authority.py tests/test_alfred_duty.py tests/test_helen_duty.py tests/test_resident_conversation_sessions.py tests/test_resident_cards.py
```

### WP-0117

WP-0117 self-validation failed because it calls WP-0106 validation and WP-0106 still fails.

## Scope

In scope:

1. Confirm repository is on latest main before repair work begins.
2. Inspect or reproduce the current stderr/stdout captures for failing pytest commands.
3. Identify the real cause of the failures.
4. Repair the narrowest legitimate defect.
5. Preserve the passing CLI smoke checks.
6. Preserve validation coverage; do not remove pytest validation just to pass.
7. Apply the same import-path/environment fix consistently to all resident-runtime validation recipes if required.
8. Repair implementation or tests only where evidence shows they are wrong or stale.
9. Revalidate WP-0106, WP-0107, WP-0108, WP-0109, WP-0110, and WP-0117.
10. Revalidate WP-0116 because it depends on resident-path closure evidence.
11. Regenerate production-readiness and coverage artifacts.
12. Add a validation recipe for WP-0118.
13. Create a WP-0118 completion receipt.

Out of scope:

- Weakening validation semantics.
- Removing pytest commands from recipes solely to get a pass.
- Marking any resident-runtime package production-ready without passing validation.
- Fabricating completion evidence.
- Broadly redesigning resident runtime, duty runner, conversation session, or authority boundary behavior.
- Changing governance, Steward authority, Chief Architect authority, Resident authority, merge authority, or production-readiness policy.
- Reopening broad historical validation sweeps.
- Changing WP-9999 quarantine behavior except to verify it remains intact.

## Required Diagnostic Steps

First confirm exact branch and commit:

```bash
git rev-parse HEAD
git status --short
```

Then reproduce or inspect failures.

If local capture files exist, inspect them. Expected current capture patterns include:

- `runtime/validation/work_packages/captures/WP-0106_*/command_03_stderr.txt`
- `runtime/validation/work_packages/captures/WP-0107_*/command_04_stderr.txt`
- `runtime/validation/work_packages/captures/WP-0108_*/command_04_stderr.txt`
- `runtime/validation/work_packages/captures/WP-0109_*/command_02_stderr.txt`
- `runtime/validation/work_packages/captures/WP-0110_*/command_07_stderr.txt`
- `runtime/validation/work_packages/captures/WP-0117_*/command_03_stdout.txt`

If captures are not present after reset, reproduce with:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0106 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0107 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0108 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0109 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0110 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0117 --json
```

Then inspect the newly generated capture files.

## Required Repair Principles

- If the issue is import path handling, make recipe pytest invocations consistently self-contained and cross-platform.
- If the issue is pytest import-mode/package resolution, fix the invocation style, not the test intent.
- If the issue is stale test assumptions, update tests with evidence from current intended behavior.
- If the issue is runtime/generated state nondeterminism, isolate state or make the assertions deterministic.
- If the issue is implementation regression, fix the implementation.
- If multiple recipes share the same root cause, apply the repair consistently.
- Do not hide failures by converting required commands to observational commands.
- Do not lower production-readiness requirements.

## Expected Areas to Inspect

Inspect at minimum:

- `src/estate/core/work_package_validation.py`
- `src/estate/core/production_readiness_validation.py` if production-readiness behavior is implicated
- `tests/test_resident_presence.py`
- `tests/test_resident_cards.py`
- `tests/test_steward_command_center.py`
- `tests/test_alfred_duty.py`
- `tests/test_helen_duty.py`
- `tests/test_resident_conversation_sessions.py`
- `tests/test_resident_conversations.py`
- `tests/test_resident_authority.py`
- resident runtime modules touched by those tests, only if implementation is the true cause

## Required Reports

Create:

`operations/validation/backlog_burn_down/WP-0118_resident_runtime_pytest_failure_repair_report.md`

Create machine-readable companion:

`runtime/validation/backlog_burn_down/WP-0118_resident_runtime_pytest_failure_repair_report.json`

The reports must include:

- commit checked before repair
- production-readiness totals before WP-0118
- production-readiness totals after WP-0118
- exact failure cause for WP-0106
- exact failure cause for WP-0107
- exact failure cause for WP-0108
- exact failure cause for WP-0109
- exact failure cause for WP-0110
- why WP-0117 failed
- files changed
- repair classification for each affected package
- tests run
- validation commands run
- WP-0106 validation result after repair
- WP-0107 validation result after repair
- WP-0108 validation result after repair
- WP-0109 validation result after repair
- WP-0110 validation result after repair
- WP-0116 validation result after repair
- WP-0117 validation result after repair
- WP-0118 validation result
- WP-9999 quarantine status
- Helen/Alfred path status
- remaining production-readiness blockers
- recommended next action

## Required Tests

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Run the exact affected pytest groups after repair:

```bash
PYTHONPATH=src python -m pytest tests/test_resident_presence.py tests/test_resident_cards.py tests/test_steward_command_center.py
PYTHONPATH=src python -m pytest tests/test_alfred_duty.py tests/test_resident_presence.py tests/test_resident_cards.py
PYTHONPATH=src python -m pytest tests/test_helen_duty.py tests/test_resident_presence.py tests/test_resident_cards.py
PYTHONPATH=src python -m pytest tests/test_resident_conversation_sessions.py tests/test_resident_conversations.py
PYTHONPATH=src python -m pytest tests/test_resident_authority.py tests/test_alfred_duty.py tests/test_helen_duty.py tests/test_resident_conversation_sessions.py tests/test_resident_cards.py
```

Add or update targeted tests if the repair changes recipe construction, implementation behavior, or deterministic runtime behavior.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0106 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0107 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0108 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0109 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0110 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0116 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0117 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0118 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Also run baseline validations:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0102 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0105 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0111 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0114 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0115 --json
```

## Required Outputs

Update or create as applicable:

- narrow recipe/test/implementation files required to fix the failures
- validation reports for WP-0106 through WP-0110
- validation reports for WP-0116, WP-0117, and WP-0118
- `operations/validation/production_readiness_report.md`
- `runtime/validation/production_readiness_report.json`
- `operations/validation/validation_coverage_manifest.md`
- `runtime/validation/validation_coverage_manifest.json`
- `operations/validation/backlog_burn_down/WP-0118_resident_runtime_pytest_failure_repair_report.md`
- `runtime/validation/backlog_burn_down/WP-0118_resident_runtime_pytest_failure_repair_report.json`
- `collaboration/work_packages/completions/WP-0118_codex_done.json`

## WP-0118 Self-Validation Recipe

Add a recipe for WP-0118 that verifies:

- the human-readable WP-0118 repair report exists
- the machine-readable WP-0118 repair report exists and parses as JSON
- the report identifies failure causes for WP-0106, WP-0107, WP-0108, WP-0109, and WP-0110
- WP-0106 validates successfully after repair
- WP-0107 validates successfully after repair
- WP-0108 validates successfully after repair
- WP-0109 validates successfully after repair
- WP-0110 validates successfully after repair
- WP-0116 validates successfully after repair
- WP-0117 validates successfully after repair
- production-readiness validation executes successfully
- WP-9999 remains not promoted
- Helen/Alfred path status is explicitly reported
- WP-0118 completion receipt is complete

Use cross-platform Python checks only. Avoid Bash-specific loops.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0118_codex_done.json`

It must include:

- `work_package_id = WP-0118`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- commit checked before repair
- failure causes for WP-0106 through WP-0110
- why WP-0117 failed
- repair classification for each package
- files changed
- tests run
- validation commands run
- production-readiness totals before and after
- Helen/Alfred path status after repair
- WP-9999 quarantine status
- remaining blockers
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0118 is complete when:

1. WP-0106 validation passes locally.
2. WP-0107 validation passes locally.
3. WP-0108 validation passes locally.
4. WP-0109 validation passes locally.
5. WP-0110 validation passes locally.
6. WP-0117 validation passes locally.
7. WP-0116 still validates.
8. WP-9999 remains quarantined/not promoted.
9. Production-readiness totals are regenerated.
10. Existing unrelated production-ready packages remain production-ready.
11. WP-0118 validates itself and has a complete receipt.
12. No validation, governance, authority, or production-readiness semantics are weakened.

## Merge Class

Class A.

Escalate only if the work requires changing validation policy semantics, receipt schema semantics, production-readiness meaning, governance authority, Steward authority, Chief Architect authority, Resident authority, or merge authority.
