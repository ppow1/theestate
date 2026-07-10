# WP-0620 - Repair WP-0619 Validation Recipe

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-09

## Mission

Repair the missing validation recipe for WP-0619 so the Operations Runtime Service Loop can be locally validated through the standard work-package validation path.

WP-0619 is merged and implemented, but PR #196 reported that:

```text
python -m estate.cli.main validate-work-package --id WP-0619 --json
```

returned `no_recipe`.

That is workflow friction and must be fixed immediately.

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is a small repository repair. It should be implemented by Codex Cloud/Web, not Codex CLI. It only updates validation recipe registration, tests, and receipt metadata.
```

Local runtime required:

```text
false
```

Capacity note:

```text
Do not use Codex CLI. This repair is deterministic repository work.
```

## Required Reading

Read:

```text
src/estate/core/work_package_validation.py
collaboration/work_packages/pending/WP-0619_Operations_Runtime_Service_Loop.md
collaboration/work_packages/completions/WP-0619_codex_done.json
docs/integration/operations_runtime_service_loop.md
```

## Scope

Implement a WP-0619 validation recipe in `src/estate/core/work_package_validation.py`.

The recipe should validate:

1. Required WP-0619 files exist.
2. Operations runtime modules compile.
3. Operations runtime deterministic tests pass.
4. Operations runtime CLI commands work.
5. Completion receipt exists and reports no provider or dispatch execution.
6. Work-package validation for WP-0619 returns `validation_status: passed`, not `no_recipe`.

## Expected Required Files

At minimum the recipe should require:

```text
src/estate/core/operations_runtime.py
src/estate/core/operations_runtime_service.py
tests/test_operations_runtime.py
tests/test_operations_runtime_service.py
docs/integration/operations_runtime_service_loop.md
collaboration/work_packages/completions/WP-0619_codex_done.json
```

## Expected Commands

Add a recipe similar to:

```python
"WP-0619": {
    "recipe_id": "wp-0619-operations-runtime-service-loop",
    "title": "WP-0619 — Operations Runtime Service Loop",
    "description": "Validates operations runtime service loop, CLI, heartbeat/status/report artifacts, documentation, and completion receipt without live providers.",
    "required_checks": [
        "Required files exist",
        "Operations runtime modules compile",
        "Deterministic tests pass",
        "CLI run-once/status/report works",
        "Receipt exists and reports no provider/dispatch execution",
    ],
    "observational_checks": [],
    "expected_artifacts": [
        "src/estate/core/operations_runtime.py",
        "src/estate/core/operations_runtime_service.py",
        "tests/test_operations_runtime.py",
        "tests/test_operations_runtime_service.py",
        "docs/integration/operations_runtime_service_loop.md",
        "collaboration/work_packages/completions/WP-0619_codex_done.json",
    ],
    "failure_criteria": [
        "Any required command exits non-zero",
        "Provider or dispatch execution is reported",
    ],
    "success_criteria": [
        "Operations runtime produces governed cycles, heartbeat/status/report artifacts, and no authority execution",
    ],
    "continue_on_failure": True,
    "commands": [
        _cmd("python -c \"from pathlib import Path; paths=['src/estate/core/operations_runtime.py','src/estate/core/operations_runtime_service.py','tests/test_operations_runtime.py','tests/test_operations_runtime_service.py','docs/integration/operations_runtime_service_loop.md','collaboration/work_packages/completions/WP-0619_codex_done.json']; missing=[p for p in paths if not Path(p).is_file()]; assert not missing, missing\""),
        _cmd("python -m py_compile src/estate/core/operations_runtime.py src/estate/core/operations_runtime_service.py"),
        _cmd("pytest -q tests/test_operations_runtime.py tests/test_operations_runtime_service.py --basetemp Temp/pytest-operations-runtime"),
        _cmd("python -m estate.cli.main operations-runtime run-once --json"),
        _cmd("python -m estate.cli.main operations-runtime status --json"),
        _cmd("python -m estate.cli.main operations-runtime report"),
        _cmd("python -c \"import json; from pathlib import Path; data=json.loads(Path('collaboration/work_packages/completions/WP-0619_codex_done.json').read_text(encoding='utf-8')); assert data.get('work_package_id') == 'WP-0619'; assert data.get('provider_execution_performed') is False; assert data.get('dispatch_execution_performed') is False\""),
    ],
},
```

Adjust command names only if the actual WP-0619 CLI names differ.

## Out of Scope

Do not redesign WP-0619.
Do not add new runtime behavior.
Do not create a new validator.
Do not change Operations Runtime authority boundaries.
Do not perform provider execution.
Do not perform dispatch execution.

## Expected Artifacts

Expected changed files:

```text
src/estate/core/work_package_validation.py
collaboration/work_packages/completions/WP-0620_codex_done.json
```

Optional changed files if existing tests require explicit recipe coverage:

```text
tests/test_work_package_validation.py
```

## Validation Commands

Run:

```powershell
Clear-Host
cd A:\theestate
python -m py_compile src\estate\core\work_package_validation.py
python -m estate.cli.main validate-work-package --id WP-0619 --json
python -m estate.cli.main validate-work-package --id WP-0620 --json
```

Also run the WP-0619 focused validation commands if not already included by the recipe:

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_operations_runtime.py tests/test_operations_runtime_service.py --basetemp Temp/pytest-operations-runtime
python -m estate.cli.main operations-runtime run-once --json
python -m estate.cli.main operations-runtime status --json
python -m estate.cli.main operations-runtime report
```

## Acceptance Criteria

This repair is complete when:

```text
validate-work-package --id WP-0619 returns validation_status: passed
validate-work-package --id WP-0619 does not return no_recipe
WP-0619 production_readiness is true, unless only blocked by pre-existing receipt metadata
provider_execution_performed remains false
dispatch_execution_performed remains false
WP-0620 completion receipt exists
```

## Completion Receipt Requirements

Create:

```text
collaboration/work_packages/completions/WP-0620_codex_done.json
```

The receipt must include validator-accepted fields:

```text
work_package_id
provider
codex_status
completed_at
branch
summary
files_changed
tests_run
validation_commands_run
known_limitations
ready_for_ca_review
pull_request_url or pull_request_not_applicable_reason
merge_authority or merge_authority_equivalent
provider_execution_performed
dispatch_execution_performed
```

## Completion Signal

Create the completion receipt and report the WP-0619 validation result.
