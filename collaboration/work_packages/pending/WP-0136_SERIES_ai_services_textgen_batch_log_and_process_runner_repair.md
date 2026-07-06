# SERIES TASK WP-0136 - AI Services TextGen Batch Log and Process Runner Repair

## Codex Command

Read collaboration/work_packages/pending/WP-0136_SERIES_ai_services_textgen_batch_log_and_process_runner_repair.md and do exactly what it says.

## Mode

SERIES

## Mission

Repair the AI Services TextGen governed launch path after WP-0134 and WP-0135 validation showed that structured batch planning is active, but the governed launch still fails health and the TextGen control-plane log is stale or misleading.

## Evidence

Local validation after WP-0135 showed:

1. The registry and dry-run planner now use `command_type = windows_batch`.
2. The planned subprocess argument vector is structured and uses the TextGen batch launcher from `A:\AI\TextGen\textgen-4.9`.
3. The governed launch records `process_start_attempted`, `process_started`, and `health_check_started`.
4. The health check fails with `urlerror` after repeated attempts.
5. Runtime state ends at `services.textgen.status = health_failed` and `processes.textgen.current_status = exited_or_unhealthy`.
6. Port 5000 is empty after the governed run.
7. The control-plane TextGen log tail still contains old nested PowerShell text and old interrupt prompts, which does not match the current structured batch command.

The control plane is truthfully reporting failure, but the diagnostic log is not proving what the current child process actually emitted. WP-0136 must repair process-runner diagnostics and make governed launch failure evidence trustworthy.

## Problem Statement

The TextGen launcher works manually, and the Estate planner now renders the correct structured batch operation. However, the Estate-governed launch still fails health. Current diagnostics are insufficient because the log file appears to contain stale content from earlier pre-WP-0134 attempts rather than current child output.

This creates two operational problems:

1. We cannot distinguish a child process startup failure from stale log contamination.
2. The control plane cannot provide enough evidence to determine whether the Windows batch child exited, failed to spawn its Python child, inherited a bad console/session state, or wrote nothing.

## Preconditions

1. WP-0133, WP-0134, and WP-0135 are merged.
2. Inspect `src/estate/ai_services/execution.py`.
3. Inspect `runtime/ai_services/implementations/textgen/service.manifest.json`.
4. Inspect tests in `tests/test_ai_services_control_plane.py`.
5. Do not remove Steward approval.
6. Do not remove post-launch health checks.
7. Do not change public binding policy.
8. Do not install, update, or remove TextGen.
9. Tests must use mocks and must not launch third-party AI services.

If a precondition fails, stop and report the blocker.

## Scope

In scope:

1. Make per-launch AI Services logs trustworthy.
2. Ensure the log for a new launch is either rotated, truncated, or given a unique per-attempt path before process start.
3. Record the exact log path in state, audit, and returned JSON.
4. Capture child process output in the selected log path.
5. Record process exit status when the launched parent process exits before health succeeds.
6. Where practical, record whether the process is still alive during diagnostics.
7. Improve diagnostics so `health_failed` can distinguish stale logs from current child output.
8. Preserve WP-0134 structured Windows batch command planning.
9. Preserve WP-0135 interrupted-health cleanup behavior.
10. Add regression tests for fresh log handling and process-exit diagnostics.

Out of scope:

- Installing or modifying TextGen.
- Changing the model file.
- Removing approval or health checks.
- Public network exposure.
- Full process supervisor redesign.
- Service-specific GUI automation.

## Required Behavior

A governed TextGen launch attempt must produce diagnostics that clearly identify the current attempt.

At minimum, the returned execution diagnostics and audit diagnostics must include:

- service id;
- operation;
- pid;
- working directory;
- command label;
- log path for the current attempt;
- log tail from the current attempt only;
- whether the process is alive at failure time if available;
- process exit code if available;
- health endpoint;
- health status and error.

The log tail must not be polluted by stale output from earlier attempts.

## Suggested Implementation Direction

Use one of these approaches:

1. Per-attempt log files under `runtime/ai_services/logs/`, such as `textgen-<timestamp>-<pid-or-attempt>.log`.
2. Truncate the service log at the start of a new execution attempt and record that truncation in audit.

Per-attempt logs are preferred because they preserve history while making current diagnostics unambiguous.

If the runner can retain a process handle safely, expose a runner method to check process return code or process status. If not, add a conservative diagnostic path that records what can be known without inventing success.

## Required Tests

Add or update tests proving:

1. A new execution attempt does not reuse stale log tail from previous attempts.
2. State records the current attempt log path.
3. Audit diagnostics use the current attempt log path.
4. Health failure diagnostics include current log tail only.
5. If the launched process exits before health succeeds, diagnostics include that fact where available.
6. WP-0134 windows batch planning remains unchanged.
7. WP-0135 interrupted-health behavior remains unchanged.
8. Existing AI Services success and health failure tests continue to pass.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest -q tests/test_ai_services_control_plane.py
PYTHONPATH=src pytest -q tests/test_work_package_validation.py tests/test_production_readiness_validation.py
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If a validation recipe is missing for WP-0136, document the exact limitation.

## Required Artifacts

Create:

```text
operations/ai_services/WP-0136_ai_services_textgen_batch_log_and_process_runner_repair_report.md
runtime/ai_services/WP-0136_ai_services_textgen_batch_log_and_process_runner_repair_report.json
collaboration/work_packages/completions/WP-0136_codex_done.json
```

## Acceptance Criteria

WP-0136 is complete when failed governed TextGen launch diagnostics are trustworthy for the current launch attempt, stale log contamination is eliminated, health failure records current child output or current absence of child output, and existing structured launcher and interruption handling semantics remain passing.

## Merge Class

Class A. Escalate only if implementation requires changing approval authority, public network exposure, cloud policy, resident authority boundaries, production-readiness semantics, or third-party installation behavior.
