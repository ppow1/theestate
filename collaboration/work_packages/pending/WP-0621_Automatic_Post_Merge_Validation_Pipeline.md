# WP-0621 - Automatic Post-Merge Validation Pipeline

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-09

## Mission

Complete the first end-to-end automatic post-merge validation loop for the Estate.

Current state:

```text
merge detected
  -> background request created
  -> runtime cycle records request
  -> manual intervention still required
```

Required state:

```text
merge detected
  -> audit request claimed
  -> clean validation workspace synchronized
  -> requested work package validated
  -> production readiness read
  -> Ring 2 prompt generated
  -> verdict written
  -> Office/background status updated
```

This package must close that gap.

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository implementation work across Post-Merge Audit, Operations Runtime, validation execution, CLI, tests, and documentation. It should be implemented by Codex Cloud/Web and validated locally after merge.
```

Local runtime required:

```text
false for implementation; true for the post-merge demonstration
```

Capacity note:

```text
Do not use Codex CLI for normal implementation. Deterministic tests must not require Ollama or live network access.
```

## Architectural Boundary

This pipeline automates validation mechanics, not institutional acceptance.

```text
Operations Runtime coordinates.
Post-Merge Audit runs deterministic validation.
Ring 2 produces reasoning evidence.
Chief Architect / Steward accepts institutional truth.
```

The pipeline must not execute providers, execute dispatch work, merge code, commit repairs, or create Steward acceptance.

## Required Scope

Implement:

1. Pending post-merge audit request consumer.
2. Request claim and duplicate-processing protection.
3. Clean validation workspace preparation.
4. Base-branch and expected-revision verification.
5. Standard `validate-work-package` execution for the requested WP.
6. Production-readiness and receipt-status collection.
7. Ring 2 prompt generation.
8. Optional local Ollama review only when explicitly enabled.
9. Final audit verdict writer.
10. Operations Runtime cycle integration.
11. Office/background status integration.
12. CLI commands for processing and demonstration.
13. Deterministic tests and documentation.

## Clean Validation Workspace

Do not use the active development tree as the normal audit workspace.

Use a configured worktree or dedicated clone path. Suggested operational default:

```text
A:\EstateRuntime\workspaces\audit\<target_id>
```

Tests must use temporary directories.

Active-tree dirtiness must be reported, not stashed or repaired.

## Validation Evidence Root

Transient command output and Ring 2 attempts should default outside the source repository.

Suggested operational default:

```text
A:\EstateRuntime\validation\<target_id>
```

Support subdirectories such as:

```text
reports
ring2
captures
handoff
archive
```

## Audit Request States

Support:

```text
pending
claimed
running_validation
ring2_required
running_ring2
completed
blocked
failed
```

Record request state, target, work package, workspace, validation result, Ring 2 paths, verdict path, warnings, and errors.

## Validation Execution

Use the existing validator:

```powershell
python -m estate.cli.main validate-work-package --id <WP-ID> --json
```

Collect:

```text
validation_status
production_ready
receipt_status
failures
findings
warnings
artifact paths
```

Do not create a second validation engine.

## Ring 2

Always generate a Ring 2 prompt when required.

Run Ollama only when explicitly enabled and available. Deterministic tests must not call Ollama.

If Ring 2 is not run, verdict should remain:

```text
ring2_required
```

If Ring 2 runs, preserve its output as evidence and produce a bounded verdict such as:

```text
accepted
accepted_with_notes
needs_repair
blocked
```

These verdicts remain evidence pending Chief Architect / Steward acceptance.

## Operations Runtime Integration

Extend runtime cycle modes:

```text
observe-only
process-audits
process-audits-and-ring2
```

Default may remain observe-only. Development-session startup must be able to enable `process-audits`.

Add cycle metrics for claimed/completed/blocked audits, validation pass/fail, Ring 2 prompts, reviews, and published verdicts.

## CLI Requirements

Suggested commands:

```powershell
python -m estate.cli.main post-merge-audit process-next --json
python -m estate.cli.main post-merge-audit process-all --max 10 --json
python -m estate.cli.main post-merge-audit demonstrate --work-package WP-0620 --pr 199 --json
python -m estate.cli.main operations-runtime run-once --process-audits --json
python -m estate.cli.main operations-runtime start --process-audits --max-cycles 10 --interval-seconds 30 --json
```

Follow existing CLI conventions if names differ.

## Demonstration Requirement

After merge, provide a real demonstration using WP-0620 / PR #199 or another recent package.

The demonstration must show:

```text
request recognized
clean workspace synchronized
merge/work package verified
validation recipe executed
production readiness read
Ring 2 prompt generated
verdict written
Office/background status updated
```

## Office / Command Center

Expose:

```text
automatic_validation_available
pending_audit_requests
running_audit_request
latest_completed_audit
latest_validation_status
latest_production_ready
latest_ring2_status
latest_verdict
latest_verdict_artifact
validation_workspace_health
validation_evidence_root
```

## Expected Artifacts

Expected files:

```text
src/estate/core/post_merge_audit_processor.py
src/estate/core/post_merge_validation_pipeline.py
tests/test_post_merge_audit_processor.py
tests/test_post_merge_validation_pipeline.py
docs/integration/automatic_post_merge_validation_pipeline.md
```

Expected integration touchpoints:

```text
src/estate/core/post_merge_audit.py
src/estate/core/post_merge_audit_runtime.py
src/estate/core/operations_runtime.py
src/estate/core/operations_runtime_service.py
src/estate/core/background_operations_runtime.py
src/estate/core/steward_command_center.py
src/estate/cli/main.py
src/estate/core/work_package_validation.py
```

## Test Requirements

Tests must cover:

- pending request claimed once,
- duplicate request not processed twice,
- temporary clean workspace prepared,
- active-tree dirtiness does not cause stash,
- wrong revision or missing file blocks audit,
- standard validator invoked,
- validation pass without Ring 2 yields `ring2_required`,
- validation failure yields `validation_failed`,
- production readiness false blocks acceptance,
- Ring 2 prompt generated,
- Ollama disabled by default,
- verdict artifact written,
- request state updated,
- runtime cycle metrics updated,
- Office summary updated,
- provider execution remains false,
- dispatch execution remains false.

## Validation Rings

### Ring 0

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\post_merge_audit_processor.py
Test-Path src\estate\core\post_merge_validation_pipeline.py
Test-Path tests\test_post_merge_audit_processor.py
Test-Path tests\test_post_merge_validation_pipeline.py
Test-Path docs\integration\automatic_post_merge_validation_pipeline.md
python -m py_compile src\estate\core\post_merge_audit_processor.py
python -m py_compile src\estate\core\post_merge_validation_pipeline.py
```

### Ring 1

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_post_merge_audit_processor.py tests/test_post_merge_validation_pipeline.py --basetemp Temp/pytest-post-merge-validation-pipeline
python -m estate.cli.main validate-work-package --id WP-0621 --json
```

### Ring 2

Review whether the package completes merge-to-verdict flow, uses a clean workspace, reuses the standard validator, preserves Steward acceptance, and avoids provider/dispatch execution.

### Ring 3

Use only if Ring 1 and Ring 2 are insufficient.

### Ring 4

Chief Architect / Steward acceptance confirms a merged package can flow automatically from merge detection to a published validation verdict without manual Git recovery.

## Completion Receipt

Create:

```text
collaboration/work_packages/completions/WP-0621_codex_done.json
```

Receipt must report:

```text
provider_execution_performed: false
dispatch_execution_performed: false
automatic_audit_requests_processed
demonstration_work_package
demonstration_verdict
validation_workspace_used
external_evidence_root_used
```

## Promotion Criteria

Ready when pending audit requests are consumed, clean workspace is used, standard validation runs, Ring 2 prompt is generated, verdict is written, Office/background status updates, deterministic tests pass, production readiness is true, and no provider or dispatch execution occurs.
