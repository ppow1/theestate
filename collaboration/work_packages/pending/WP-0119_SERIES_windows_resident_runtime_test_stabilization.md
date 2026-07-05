# SERIES TASK WP-0119 — Windows Resident Runtime Test Stabilization

## Codex Command

Read collaboration/work_packages/pending/WP-0119_SERIES_windows_resident_runtime_test_stabilization.md and do exactly what it says.

## Mode

SERIES

## Mission

Repair the remaining Windows-local resident runtime validation failures discovered after pytest was installed locally and WP-0118 was verified on latest main.

The resident runtime path is no longer failing because pytest is missing or because the `estate` package cannot be imported. Local validation now reaches the actual tests. The remaining failures are specific Windows/local behavioral mismatches:

1. `steward-command-center --json` reports the Alfred resident card as available but does not create `runtime/steward/command_center.html` in the temp working directory used by the test.
2. `helen-duty --json` returns Windows backslash paths in `runtime_artifacts.duty_state` where the test expects canonical repository-style forward-slash paths.

This package must repair those precise defects without weakening validation semantics, without removing test coverage, and without changing governance or authority semantics.

## Background

After WP-0118 merged, the local machine was confirmed to be on latest main:

- commit: `6eb0c92d3c4ac306b80facc0ecaaed3739fb0c11`
- merge: PR #123 / WP-0118

Local environment was repaired:

- Python: `C:\Python314\python.exe`
- Python version: `3.14.6`
- pytest installed: `9.1.1`

After installing pytest, validation improved:

- WP-0107 passed and became ready.
- WP-0109 passed and became ready.
- WP-0116 passed and remained ready.

Still blocked locally:

- WP-0106
- WP-0108
- WP-0110
- WP-0117, because it depends on WP-0106
- WP-0118, because it depends on WP-0106 and resident runtime path validation

## Observed Failures

### WP-0106 failure

Failing test:

`tests/test_steward_command_center.py::test_command_center_cli_generates_json`

Failure:

```text
assert (tmp_path / "runtime/steward/command_center.html").exists()
```

Observed behavior:

- The CLI command succeeds.
- The JSON payload indicates `payload["panels"]["alfred_resident_card"]["available"] is True`.
- The expected HTML artifact is not created under the temporary test workspace.

Required interpretation:

This is a real test/implementation contract mismatch. Determine whether the command should write the HTML artifact whenever invoked, or whether the test expectation is stale. Repair according to intended Operations Console behavior, preserving useful artifact generation coverage.

### WP-0108 and WP-0110 failure

Failing test:

`tests/test_helen_duty.py::test_helen_duty_cli_json`

Failure:

```text
assert payload["runtime_artifacts"]["duty_state"] == "runtime/helen/duty_state.json"
```

Observed local payload:

```text
runtime\helen\duty_state.json
```

Expected payload:

```text
runtime/helen/duty_state.json
```

Required interpretation:

The resident duty runtime should expose stable, repository-style JSON artifact paths that are platform-independent. Internally the filesystem may use `Path`, but emitted JSON contracts should be canonical forward-slash paths unless existing Estate standards explicitly say otherwise.

## Scope

In scope:

1. Inspect the command center implementation and tests.
2. Determine why `steward-command-center --json` does not write `runtime/steward/command_center.html` in the temp working directory.
3. Repair the command center implementation or the test only according to the intended command contract.
4. Inspect Helen duty runtime JSON output.
5. Normalize emitted runtime artifact paths to canonical forward-slash strings where appropriate.
6. Ensure Alfred duty and Helen duty output contracts remain consistent.
7. Re-run affected tests.
8. Re-run validation for WP-0106, WP-0108, WP-0110, WP-0117, WP-0118, and WP-0119.
9. Re-run WP-0107 and WP-0109 to ensure already-passing resident runtime packages remain passing.
10. Re-run WP-0116 because it depends on final exception closure evidence.
11. Regenerate production-readiness and coverage artifacts.
12. Create a WP-0119 validation recipe and completion receipt.

Out of scope:

- Removing or downgrading pytest validation commands.
- Converting required validation commands to observational commands merely to pass.
- Fabricating readiness evidence.
- Changing Chief Architect, Steward, Resident, HR, mailbox, personnel, governance, or merge authority semantics.
- Broadly redesigning Operations Console behavior.
- Broadly redesigning resident duty runtime behavior.
- Reopening historical validation sweeps.
- Changing WP-9999 quarantine behavior except to verify it remains not promoted.

## Required Repair Principles

- Prefer fixing implementation where the test expresses a valid artifact/output contract.
- Prefer fixing tests only where they encode an invalid platform-specific assumption.
- Do not remove the artifact-existence check unless the command's documented contract clearly states it should not write the artifact.
- Preserve stable JSON contracts for CLI consumers.
- Normalize externally emitted artifact paths to canonical forward-slash form when they are repository-relative contract values.
- Keep filesystem writes cross-platform.
- Keep tests deterministic under temporary working directories.

## Required Files to Inspect

Inspect at minimum:

- `src/estate/core/work_package_validation.py`
- `src/estate/cli/main.py`
- stewardship / command center implementation modules
- Helen duty runtime implementation modules
- Alfred duty runtime implementation modules if path normalization should be consistent
- `tests/test_steward_command_center.py`
- `tests/test_helen_duty.py`
- `tests/test_alfred_duty.py`
- `tests/test_resident_authority.py`

## Required Tests

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
```

Run the exact affected tests:

```bash
PYTHONPATH=src python -m pytest tests/test_resident_presence.py tests/test_resident_cards.py tests/test_steward_command_center.py
PYTHONPATH=src python -m pytest tests/test_helen_duty.py tests/test_resident_presence.py tests/test_resident_cards.py
PYTHONPATH=src python -m pytest tests/test_resident_authority.py tests/test_alfred_duty.py tests/test_helen_duty.py tests/test_resident_conversation_sessions.py tests/test_resident_cards.py
```

Also run the already-repaired resident packages to guard against regression:

```bash
PYTHONPATH=src python -m pytest tests/test_alfred_duty.py tests/test_resident_presence.py tests/test_resident_cards.py
PYTHONPATH=src python -m pytest tests/test_resident_conversation_sessions.py tests/test_resident_conversations.py
```

Add targeted tests if the implementation changes path normalization or command center artifact generation.

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
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0119 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Also verify pytest is available in the validation Python environment:

```bash
python -c "import pytest; print(pytest.__version__)"
```

## Required Reports

Create:

`operations/validation/backlog_burn_down/WP-0119_windows_resident_runtime_test_stabilization_report.md`

Create machine-readable companion:

`runtime/validation/backlog_burn_down/WP-0119_windows_resident_runtime_test_stabilization_report.json`

The reports must include:

- commit checked before repair
- local Python executable/version if available
- pytest availability/version if available
- exact WP-0106 failure cause
- exact WP-0108 failure cause
- exact WP-0110 failure cause
- why WP-0117 and WP-0118 failed transitively
- repair classification for command center artifact generation
- repair classification for duty runtime artifact path normalization
- files changed
- tests run
- validation commands run
- production-readiness totals before and after
- WP-0106 validation result after repair
- WP-0107 validation result after repair
- WP-0108 validation result after repair
- WP-0109 validation result after repair
- WP-0110 validation result after repair
- WP-0116 validation result after repair
- WP-0117 validation result after repair
- WP-0118 validation result after repair
- WP-0119 validation result
- WP-9999 quarantine status
- Alfred/Helen runtime path status
- remaining blockers
- recommended next action

## Required Outputs

Update or create as applicable:

- narrow implementation/test files required for the command-center artifact fix
- narrow implementation/test files required for path normalization
- `src/estate/core/work_package_validation.py` for WP-0119 recipe registration
- relevant tests
- validation reports for repaired packages under `operations/validation/reports/`
- runtime validation JSON for repaired packages under `runtime/validation/work_packages/`
- `operations/validation/production_readiness_report.md`
- `runtime/validation/production_readiness_report.json`
- `operations/validation/validation_coverage_manifest.md`
- `runtime/validation/validation_coverage_manifest.json`
- `operations/validation/backlog_burn_down/WP-0119_windows_resident_runtime_test_stabilization_report.md`
- `runtime/validation/backlog_burn_down/WP-0119_windows_resident_runtime_test_stabilization_report.json`
- `collaboration/work_packages/completions/WP-0119_codex_done.json`

## WP-0119 Self-Validation Recipe

Add a recipe for WP-0119 that verifies:

- the human-readable WP-0119 report exists
- the machine-readable WP-0119 report exists and parses as JSON
- the report identifies WP-0106, WP-0108, and WP-0110 failure causes
- WP-0106 validates successfully after repair
- WP-0107 remains passing
- WP-0108 validates successfully after repair
- WP-0109 remains passing
- WP-0110 validates successfully after repair
- WP-0116 validates successfully after repair
- WP-0117 validates successfully after repair
- WP-0118 validates successfully after repair
- production-readiness validation executes successfully
- WP-9999 remains not promoted
- Alfred/Helen runtime path status is explicitly reported
- WP-0119 completion receipt is complete

Use cross-platform Python checks only. Avoid Bash-specific loops.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0119_codex_done.json`

It must include:

- `work_package_id = WP-0119`
- `codex_status = done`
- `completed_at`
- `branch`
- `pull_request_url` or `pull_request_url_not_applicable_reason`
- `summary`
- commit checked before repair
- failure causes for WP-0106, WP-0108, WP-0110
- transitive failure cause for WP-0117 and WP-0118
- repair classifications
- files changed
- tests run
- validation commands run
- production-readiness totals before and after
- Alfred/Helen runtime path status after repair
- WP-9999 quarantine status
- remaining blockers
- known limitations
- `ready_for_ca_review = true`
- `merge_authority = ca_verified_auto_merge_allowed`

## Acceptance Criteria

WP-0119 is complete when:

1. WP-0106 validation passes locally.
2. WP-0107 remains passing locally.
3. WP-0108 validation passes locally.
4. WP-0109 remains passing locally.
5. WP-0110 validation passes locally.
6. WP-0117 validation passes locally.
7. WP-0118 validation passes locally.
8. WP-0116 still validates.
9. WP-9999 remains quarantined/not promoted.
10. Production-readiness totals are regenerated.
11. Existing unrelated production-ready packages remain production-ready.
12. WP-0119 validates itself and has a complete receipt.
13. No validation, governance, authority, or production-readiness semantics are weakened.

## Merge Class

Class A.

Escalate only if the work requires changing validation policy semantics, receipt schema semantics, production-readiness meaning, governance authority, Steward authority, Chief Architect authority, Resident authority, or merge authority.
