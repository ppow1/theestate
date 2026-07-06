# SERIES TASK WP-0133 — AI Services Post-Launch Health Verification and Process Tracking Repair

## Codex Command

Read collaboration/work_packages/pending/WP-0133_SERIES_ai_services_post_launch_health_and_process_tracking_repair.md and do exactly what it says.

## Mode

SERIES

## Mission

Repair the AI Services Control Plane execution semantics so service operations are not marked successful merely because a process ID was returned.

WP-0132 added governed execution adapters and approved TextGen model-load execution. Steward validation showed that the control plane returned `result = executed` and recorded `execution_succeeded` with PID 34908, but the TextGen endpoint at `http://127.0.0.1:5000/v1/models` refused connection immediately afterward. The tracked PID was no longer present, no listener existed on port 5000, and the service log contained only the attempted command.

WP-0133 must add post-launch health verification, process liveness checks, clearer lifecycle states, and better diagnostics for failed service launches.

## Problem Statement

The current WP-0132 execution adapter treats process creation as service success. This is insufficient. A local service may spawn and exit immediately, fail before binding its endpoint, launch a child process, or return before the actual server is healthy.

During Steward validation:

```text
ai-services load-model --service textgen --model Qwen3-8B-Q6_K.gguf --approved-by steward --json
```

returned:

```text
result: executed
approval_state: executed
execution.pid: 34908
service_id: textgen
operation: load_model
```

but the follow-up endpoint check failed:

```text
Invoke-RestMethod http://127.0.0.1:5000/v1/models
No connection could be made because the target machine actively refused it.
```

State recorded TextGen as running even though there was no live endpoint:

```text
runtime/ai_services/state.json
services.textgen.status = running
processes.textgen.pid = 34908
```

Follow-up diagnostics showed:

```text
Estate tracked PID: none
Port 5000 listener: none
Estate AI Services TextGen log: only the attempted command
```

This is a correctness defect in the control plane lifecycle model.

## Preconditions

1. Confirm WP-0131 and WP-0132 are merged.
2. Inspect `src/estate/ai_services/execution.py`, `control.py`, `policy.py`, `discovery.py`, and `tests/test_ai_services_control_plane.py`.
3. Inspect TextGen manifest at `runtime/ai_services/implementations/textgen/service.manifest.json`.
4. Inspect the existing audit log and state behavior.
5. Do not move model files.
6. Do not install, update, or remove third-party AI applications.
7. Do not expose any control API outside loopback.
8. Do not add cloud API behavior.
9. Tests must use mocks and must not launch actual AI services.

If any precondition fails, stop and report the exact blocker.

## Scope

In scope:

1. Add post-launch health verification for services with declared health/status endpoints.
2. Add process liveness checks after launch.
3. Replace immediate `execution_succeeded` semantics with lifecycle-aware results.
4. Add explicit states such as `process_started`, `health_pending`, `healthy`, `health_failed`, `process_exited`, and `execution_failed` or equivalent existing Estate terms.
5. Update state writing so a service is not marked `running` until health verification succeeds.
6. Record failed launches accurately in `runtime/ai_services/state.json`.
7. Improve audit logging to distinguish process start from service health success.
8. Capture launch diagnostics when the process exits quickly.
9. Make TextGen launch validation fail clearly if no listener appears on port 5000 or `/v1/models` refuses connection.
10. Preserve Steward approval and Alfred bounded-request behavior.
11. Add tests for process-start-but-health-fails behavior.
12. Add WP-0133 validation recipe, report, and completion receipt.

Out of scope:

- Changing the broader Estate authority model.
- Moving or consolidating model files.
- Installing or updating TextGen.
- Installing models.
- Public network exposure.
- Cloud APIs.
- Full UI repair.
- ComfyUI workflow execution.
- SillyTavern session automation.

## Required Behavior

### Launch lifecycle

A service launch should progress through explicit lifecycle stages. Equivalent behavior is required:

1. `execution_requested`
2. `approval_verified`
3. `process_start_attempted`
4. `process_started` when a PID is returned
5. `health_pending` while endpoint checks are running
6. `healthy` only when declared health/status check succeeds
7. `health_failed` when endpoint refuses connection, times out, or returns invalid response
8. `process_exited` when the process exits before health succeeds
9. `execution_failed` when no safe process can be started

The exact field names may follow existing Estate conventions, but the semantics must be represented.

### Health check policy

For each service with a declared `status` operation containing an HTTP endpoint, execution must attempt health verification after process start.

Minimum requirements:

- Use loopback-only endpoint validation.
- Use a bounded timeout.
- Use a bounded retry interval.
- Do not hang indefinitely.
- Record the final health result in state and audit log.
- Do not mark service status `running` until health succeeds.

### State semantics

If a process starts but endpoint health fails:

```json
{
  "services": {
    "textgen": {
      "status": "health_failed",
      "endpoint": "http://127.0.0.1:5000/v1",
      "last_operation": "load_model"
    }
  },
  "processes": {
    "textgen": {
      "current_status": "exited_or_unhealthy",
      "pid": 34908,
      "health_status": "failed",
      "health_error": "connection_refused"
    }
  }
}
```

This example is illustrative. Use the existing state schema if one exists, but preserve the distinction between PID creation and service health.

### Audit semantics

Audit log must distinguish:

- `execution_attempted`
- `process_started`
- `health_check_started`
- `health_check_succeeded`
- `health_check_failed`
- `process_exited_before_health`
- `execution_succeeded` only after health success
- `execution_failed` when process or health failed

### TextGen-specific requirement

For TextGen, health success requires `http://127.0.0.1:5000/v1/models` to respond successfully after the launch command.

If TextGen exits immediately or never binds port 5000, the operation must not return `result = executed`. It should return a failed or unhealthy result with diagnostic fields.

### Diagnostics requirement

When launch fails or health fails, include diagnostic data such as:

- tracked PID;
- whether the PID is still alive;
- expected endpoint;
- expected port;
- last health error;
- log path;
- short tail of captured launch log if safe and available;
- command label or redacted command representation.

Do not expose secrets in diagnostics.

## CLI Requirements

The existing commands should continue to work:

```bash
PYTHONPATH=src python -m estate.cli.main ai-services status --json
PYTHONPATH=src python -m estate.cli.main ai-services rediscover --json
PYTHONPATH=src python -m estate.cli.main ai-services load-model --service textgen --model Qwen3-8B-Q6_K.gguf --approved-by steward --json
```

For real execution, the JSON response must distinguish process start from endpoint health.

Add optional launch-health parameters only if they fit existing CLI conventions, such as:

```bash
--health-timeout-seconds 30
--health-interval-seconds 2
```

Defaults must be safe and bounded.

## API Requirements

If AI Services API execution endpoints are active, update their response semantics to match the CLI lifecycle states. Do not expose the API beyond loopback.

## Required Tests

Add or update tests for:

1. Process runner returns a PID but health endpoint fails; result is not `executed`/success.
2. Process runner returns a PID and mocked health succeeds; result is `executed` or equivalent success.
3. State is not marked `running` until health succeeds.
4. State records `health_failed` when endpoint refuses connection.
5. Audit log records `process_started` and `health_check_failed` separately.
6. Audit log records `health_check_succeeded` before `execution_succeeded` on success.
7. TextGen model-load uses `/v1/models` as its health endpoint.
8. Quick process exit before health is reported as `process_exited_before_health` or equivalent.
9. Loopback-only policy remains enforced.
10. Cloud endpoints remain rejected by default.
11. Existing WP-0131 and WP-0132 AI Services tests remain passing.
12. Existing work-package and production-readiness validation tests remain passing.

Use mocks for process execution and health checks. Tests must not launch actual third-party AI applications.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest tests/test_ai_services_control_plane.py -q
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0133 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If CLI names differ, use existing canonical validation commands and document the mapping.

## Required Artifacts

Create:

```text
operations/ai_services/WP-0133_ai_services_post_launch_health_repair_report.md
```

Create machine-readable companion:

```text
runtime/ai_services/WP-0133_ai_services_post_launch_health_repair_report.json
```

The report must include:

- current git commit;
- files changed;
- lifecycle state model;
- health verification design;
- TextGen health endpoint behavior;
- process liveness behavior;
- state semantics;
- audit semantics;
- CLI/API response changes;
- tests run;
- validation commands run;
- known limitations;
- recommended next action.

## Required Outputs

- Post-launch health verification.
- Process liveness check after launch.
- Correct distinction between process start and service health.
- Accurate state updates for failed health.
- Improved audit events.
- TextGen-specific health verification through `/v1/models`.
- Mock-tested health success and health failure behavior.
- WP-0133 report Markdown and JSON.
- `collaboration/work_packages/completions/WP-0133_codex_done.json`.

## Completion Artifact

Create:

```text
collaboration/work_packages/completions/WP-0133_codex_done.json
```

It must include `work_package_id = WP-0133`, `codex_status = done`, summary, lifecycle states, health verification behavior, process liveness behavior, TextGen health endpoint behavior, state changes, audit changes, tests run, validation commands run, known limitations, recommended next action, `ready_for_ca_review = true`, and `merge_authority = ca_verified_auto_merge_allowed`.

## Acceptance Criteria

WP-0133 is complete when the AI Services Control Plane no longer treats PID creation as service success, verifies declared loopback health endpoints after launch, records health failures truthfully, only marks services running after health success, and preserves the local-first, Steward-approved, Alfred-bounded authority model.

## Merge Class

Class A. Escalate only if implementation requires changing cloud model policy, public network exposure policy, resident API governance, memory/redaction policy, production-readiness semantics, Alfred authority boundaries, or third-party application installation/update/removal behavior.
