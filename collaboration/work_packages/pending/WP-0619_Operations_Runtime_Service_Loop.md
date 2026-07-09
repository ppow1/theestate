# WP-0619 - Operations Runtime Service Loop

Status: Proposed  
Priority: Critical  
Owner: Chief Architect #6  
Classification: Estate Internal  
Created: 2026-07-09

## Mission

Implement the first persistent Operations Runtime service loop for the Estate.

WP-0617 created background operation cycles. WP-0618 created Operational Targets, Git hygiene, post-merge audit, and target control surfaces. WP-0619 must connect those pieces into a repeatable runtime loop that can wake, evaluate registered targets, run enabled watches, create governed requests, update Office status, and sleep again.

This package should be a large integrated step. It should not be a tiny watcher-only package.

## Provider Assignment Guidance

Recommended implementation provider:

```text
codex_cloud_web
```

Provider rationale:

```text
This is repository implementation work across background operations, operational targets, runtime loop control, CLI, status artifacts, tests, and documentation. It should be implemented by Codex Cloud/Web. It must not require live provider execution, Codex CLI, Ollama, or network access in deterministic tests.
```

Local runtime required:

```text
false for implementation; true for operational use after merge
```

Capacity note:

```text
Do not use Codex CLI for normal implementation. Validate locally with deterministic tests and Ring 2 review.
```

## Architectural Position

WP-0619 establishes the Operations Runtime as the living operational layer beneath the Office of the Steward.

The runtime loop must coordinate:

```text
Operational Target Registry
Background watch execution
Git hygiene checks
Post-merge audit requests
Validation freshness checks
Ring 2 review requests
Office status publication
Runtime health reporting
```

It must not become an execution provider, routing authority, scheduler with independent authority, or acceptance layer.

## 80/20 Direction

Build the useful operational loop now:

```text
start runtime cycle
  -> load enabled operational targets
  -> load enabled watches
  -> evaluate targets and watches
  -> create governed requests/events/status artifacts
  -> publish Office summary
  -> write heartbeat
  -> stop or sleep
```

The first implementation may be a bounded service loop with configurable max cycles, interval seconds, and dry-run mode. It does not need to be a perfect daemon.

## Required Scope

Implement:

1. Operations Runtime service model.
2. Runtime loop controller with one-shot and repeated-cycle modes.
3. Runtime heartbeat artifact.
4. Runtime lock file or guard to prevent accidental duplicate loops.
5. Configurable cycle interval and max cycle count.
6. Integration with Operational Target Registry from WP-0618.
7. Integration with Background Operations watch cycle from WP-0617.
8. Integration with post-merge audit request generation from WP-0618.
9. Office command-center status summary for runtime health.
10. CLI commands to start, run-once, status, stop-request, and report.
11. Deterministic tests that run without live providers, network calls, Ollama, or long waits.
12. Documentation for running the runtime during development sessions.

## Out of Scope

Do not implement provider execution, autonomous code repair, automatic merging, automatic commits, destructive cleanup, a new provider registry, a new dispatch queue, a new Office, or a competing event system.

This runtime may observe, evaluate, request, and report. It may not approve, accept, dispatch provider work, or make institutional truth.

## Expected Artifacts

Expected files:

```text
src/estate/core/operations_runtime.py
src/estate/core/operations_runtime_service.py
tests/test_operations_runtime.py
tests/test_operations_runtime_service.py
docs/integration/operations_runtime_service_loop.md
```

Integration touchpoints if clean:

```text
src/estate/cli/main.py
src/estate/core/background_operations.py
src/estate/core/background_operations_runtime.py
src/estate/core/operational_targets.py
src/estate/core/operational_targets_runtime.py
src/estate/core/post_merge_audit.py
src/estate/core/post_merge_audit_runtime.py
src/estate/core/steward_command_center.py
```

## Runtime Artifacts

Use local paths such as:

```text
runtime/operations_runtime/status/latest.json
runtime/operations_runtime/status/summary.json
runtime/operations_runtime/heartbeat.json
runtime/operations_runtime/lock.json
runtime/operations_runtime/reports/latest.md
runtime/operations_runtime/cycles/<cycle_id>.json
```

Transient large evidence should continue to default outside the repo under the configured validation evidence root introduced by WP-0618.

## Runtime States

Allowed runtime states:

```text
idle
starting
running
sleeping
stop_requested
stopped
blocked
failed
```

## Runtime Cycle Requirements

Each cycle should record:

```text
cycle_id
started_at
finished_at
runtime_state
targets_evaluated
watches_evaluated
requests_created
events_created
audits_requested
git_hygiene_findings
ring2_requests_created
warnings
errors
```

## CLI Requirements

Add commands using existing Estate CLI style. Suggested commands:

```powershell
python -m estate.cli.main operations-runtime run-once --json
python -m estate.cli.main operations-runtime start --max-cycles 5 --interval-seconds 30 --json
python -m estate.cli.main operations-runtime status --json
python -m estate.cli.main operations-runtime request-stop --json
python -m estate.cli.main operations-runtime report
```

If existing CLI style requires a different shape, follow repository convention and document actual commands.

## Office / Command Center Requirements

Expose summary fields such as:

```text
operations_runtime_available
operations_runtime_state
last_cycle_id
last_cycle_at
active_targets_count
enabled_watches_count
requests_created_last_cycle
audits_requested_last_cycle
git_hygiene_findings_count
ring2_requests_count
runtime_warnings
```

No fake controls. Every surfaced action must correspond to a real handler.

## Development Session Requirement

This package should support the Steward starting a local development operations loop at the beginning of a working session. The loop should help keep Git hygiene, target watches, post-merge audit requests, and validation freshness visible while development work continues.

It must avoid blocking the active development tree and must not use stash as normal behavior.

## Test Requirements

Tests must cover:

- run-once cycle produces heartbeat/status artifacts,
- repeated cycle obeys max-cycles without long waits,
- stop-request is honored,
- lock prevents duplicate runtime loops,
- enabled targets are evaluated,
- paused/disabled targets are skipped,
- watches create governed requests,
- post-merge audit-needed request can be generated,
- Office summary includes runtime status,
- no provider execution occurs,
- no dispatch execution occurs,
- no network/Ollama/Codex CLI calls occur in deterministic tests,
- active tree dirtiness is not stashed or repaired.

## Validation Rings

### Ring 0 - Static / Structural Validation

```powershell
Clear-Host
cd A:\theestate
Test-Path src\estate\core\operations_runtime.py
Test-Path src\estate\core\operations_runtime_service.py
Test-Path tests\test_operations_runtime.py
Test-Path tests\test_operations_runtime_service.py
Test-Path docs\integration\operations_runtime_service_loop.md
python -m py_compile src\estate\core\operations_runtime.py
python -m py_compile src\estate\core\operations_runtime_service.py
```

### Ring 1 - Deterministic Test Validation

```powershell
Clear-Host
cd A:\theestate
python -c "from pathlib import Path; Path('Temp').mkdir(exist_ok=True)"
pytest -q tests/test_operations_runtime.py tests/test_operations_runtime_service.py --basetemp Temp/pytest-operations-runtime
python -m estate.cli.main validate-work-package --id WP-0619 --json
```

Expected evidence:

```text
runtime/validation/work_packages/WP-0619_validation.json
operations/validation/reports/WP-0619_validation.md
collaboration/work_packages/completions/WP-0619_codex_done.json
```

### Ring 2 - Local GPU Reasoning Review

Reviewer questions:

```text
Does WP-0619 make Background Operations into a useful runtime loop rather than isolated commands?
Does it integrate Operational Targets, watches, Git hygiene, post-merge audit, and Office status?
Does it avoid provider execution and dispatch execution?
Does it avoid autonomous authority?
Does it keep active-tree dirtiness from blocking runtime status/audit behavior?
Is it ready for Chief Architect review?
```

### Ring 3 - CLI Escalation Validation

Use only if Ring 1 and Ring 2 are insufficient.

### Ring 4 - Institutional Acceptance

Chief Architect / Steward acceptance confirms the Operations Runtime can be started during a development session and produce useful background operational status without becoming an authority layer.

## Completion Receipt Requirements

Create:

```text
collaboration/work_packages/completions/WP-0619_codex_done.json
```

Receipt must include validator-accepted fields:

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

## Promotion Criteria

Ready when Ring 0 passes, Ring 1 passes, production readiness is true, Ring 2 recommends Chief Architect review, runtime loop commands work, heartbeat/status artifacts are produced, Office summary is updated, and no provider/dispatch execution occurs.

## Completion Signal

Create the completion receipt and report validation evidence paths.
