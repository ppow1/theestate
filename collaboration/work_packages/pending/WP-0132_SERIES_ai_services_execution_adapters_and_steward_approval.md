# SERIES TASK WP-0132 — AI Services Execution Adapters and Steward Approval

## Codex Command

Read collaboration/work_packages/pending/WP-0132_SERIES_ai_services_execution_adapters_and_steward_approval.md and do exactly what it says.

## Mode

SERIES

## Mission

Extend the WP-0131 AI Services Control Plane from planned/audited operations into governed local execution for approved service actions.

WP-0131 created the rediscoverable control plane, service manifests, registry/state separation, CLI/API hooks, policy gates, and local audit logging. Its stated limitation is that operations are planned/audited only and no third-party service process is launched by that work package. WP-0132 closes that gap by adding process execution adapters and a Steward approval workflow while preserving the Estate local-first boundary.

## Problem Statement

The Steward needs a practical local AI stack manager for Open WebUI, Ollama, TextGen, ComfyUI, and SillyTavern. Alfred should eventually be able to request actions such as starting a service or loading a TextGen model, but only through approved Estate control paths. The system must not regress into ad hoc launch scripts, unrestricted shell access, or public network exposure.

The next capability is to make approved AI Services Control Plane operations actually execute local service commands safely, track process state, and provide a clear Steward approval mechanism.

## Preconditions

1. Confirm WP-0131 is merged.
2. Inspect `src/estate/ai_services`, `runtime/ai_services`, `operations/ai_services`, and `tests/test_ai_services_control_plane.py`.
3. Inspect the WP-0131 completion artifact at `collaboration/work_packages/completions/WP-0131_codex_done.json`.
4. Confirm the WP-0131 limitation that operations are planned/audited only.
5. Confirm existing CLI conventions before adding or changing commands.
6. Confirm existing resident/steward UI conventions before adding any approval surface.
7. Do not move model files.
8. Do not install, update, or remove third-party AI applications.
9. Do not expose any service or control API outside loopback.
10. Do not add cloud API behavior.

If any precondition fails, stop and report the exact blocker.

## Scope

In scope:

1. Add local process execution adapters for service operations already modeled by WP-0131 manifests.
2. Add a Steward approval workflow for operations requiring authority.
3. Add dry-run/planned execution mode and real execution mode.
4. Add process state tracking for started services.
5. Add safe start behavior for modeled services.
6. Add safe stop behavior only for services started or tracked by the control plane, unless an existing manifest explicitly permits another safe method.
7. Add approved TextGen model-load execution by starting or restarting TextGen with the requested model according to its manifest.
8. Preserve Alfred as a bounded requester, not a raw process executor.
9. Preserve local audit logging for every allowed, denied, planned, and executed operation.
10. Add tests for approval, dry-run, execution adapter planning, process tracking, stop safety, and TextGen model-load execution planning.
11. Add WP-0132 validation recipe and completion receipt.

Out of scope:

- Model storage consolidation.
- Moving model files.
- Installing models automatically.
- Installing, updating, or removing local AI applications.
- Public network exposure.
- Cloud APIs.
- Full desktop GUI launcher.
- ComfyUI workflow execution.
- SillyTavern character/session automation.
- Giving Alfred unrestricted host command access.
- Bypassing Steward approval for operations marked as approval-required.

## Required Behavior

### Approval States

Implement a clear approval model for service operations. At minimum, operations should support equivalent states:

- `planned`
- `requires_approval`
- `approved`
- `denied`
- `executed`
- `failed`

The exact model may follow existing Estate conventions if found.

### Dry Run

All operations that can execute a local command must support dry-run behavior. Dry-run must return the planned operation, policy decision, target service, command template or safe description, and required approval without launching a process.

### Execution

Real execution must occur only when:

1. the service is present in the registry;
2. the requested operation is declared by the service manifest;
3. the operation passes policy;
4. required approval is present;
5. the command resolves only against manifest-declared templates and validated arguments;
6. the target host/bind policy remains loopback-only.

### Process Tracking

When the control plane starts a service, it must record process state locally, including at least:

- service id;
- operation id;
- process id if available;
- start time;
- command label or redacted command representation;
- endpoint;
- expected ports;
- current status;
- log path if captured.

State should be stored under the existing WP-0131 runtime state structure or a clearly documented extension.

### Stop Safety

Stop behavior must be conservative. The control plane may stop processes it started and tracks. It must not kill arbitrary matching processes unless the manifest and policy explicitly define that behavior and tests cover it.

### TextGen Model Load

TextGen model-load requests must use the WP-0131 manifest pattern and require approval.

Observed working local pattern:

```powershell
Set-Location A:\AI\TextGen\textgen-4.9
.\textgen.bat --nowebui --listen --model "Qwen3-8B-Q6_K.gguf" --loader llama.cpp
```

Implementation must validate the requested model name against the manifest-declared model directory before execution. Do not allow path traversal or arbitrary command injection through model names.

If a different TextGen process is already running, behavior must be explicit and conservative: either deny and report the blocker, or implement an approved restart flow with audit logging.

### Ollama

Ollama support may include status and safe start behavior if the existing environment supports it. Model loading for Ollama should remain bounded to modeled commands and must not install a model without Steward approval.

### Open WebUI

Open WebUI support should start the existing local installation using the known virtual environment only if manifest validation confirms the path. Open WebUI should not be restarted for TextGen model loads unless explicitly required by a future package.

### ComfyUI and SillyTavern

For ComfyUI and SillyTavern, implement conservative start/status support only when safe launcher detection is explicit in the manifest. Do not run arbitrary `Start.bat` by name without manifest confirmation. An earlier naive launcher attempt opened the wrong target, so this work must avoid broad filename assumptions.

## CLI Requirements

Extend or refine existing WP-0131 commands to support dry-run, approval, and execution. Equivalent behavior should exist for:

```bash
PYTHONPATH=src python -m estate.cli.main ai-services start --service textgen --dry-run
PYTHONPATH=src python -m estate.cli.main ai-services start --service textgen --approved-by steward
PYTHONPATH=src python -m estate.cli.main ai-services load-model --service textgen --model Qwen3-8B-Q6_K.gguf --dry-run
PYTHONPATH=src python -m estate.cli.main ai-services load-model --service textgen --model Qwen3-8B-Q6_K.gguf --approved-by steward
PYTHONPATH=src python -m estate.cli.main ai-services stop --service textgen --dry-run
PYTHONPATH=src python -m estate.cli.main ai-services status
```

Command names may differ if required by existing CLI conventions, but behavior must be equivalent and documented.

## API Requirements

If WP-0131 added or defined local API endpoints, extend them with approval/dry-run semantics. Equivalent behavior should exist for:

```text
POST /ai-services/services/{service_id}/start
POST /ai-services/services/{service_id}/stop
POST /ai-services/services/{service_id}/models/load
```

Request bodies must represent actor, reason, approval status, and dry-run mode. The API must bind only to loopback if it is runnable in this work package.

## Steward Approval Requirement

Create a minimal Steward approval mechanism consistent with existing Estate conventions. If an existing decision queue or approval file exists, use it. If not, create a local runtime approval artifact under the AI Services runtime area and document it.

The approval mechanism must allow a request to be recorded first, then approved or denied before execution. Alfred may create or request an approval record, but Alfred must not mark his own request approved unless an existing Estate authority model explicitly allows it.

## Audit Log Requirements

Every operation must append a structured local audit record. The audit record must distinguish:

- planned dry-run;
- approval requested;
- approval granted;
- approval denied;
- execution attempted;
- execution succeeded;
- execution failed;
- policy denied.

The audit log must remain local.

## Required Tests

Add or update tests for:

1. Dry-run start returns a plan without launching a process.
2. Start without required approval is denied or recorded as requires approval.
3. Start with approval reaches the execution adapter through a mocked process runner.
4. Process state is recorded after mocked start.
5. Stop only targets a tracked process unless manifest policy allows otherwise.
6. TextGen model-load validates the model name against the declared model directory.
7. TextGen model-load rejects path traversal and command injection strings.
8. TextGen model-load without approval is denied or recorded as requires approval.
9. TextGen model-load with approval reaches the mocked execution adapter.
10. Audit log entries are written for planned, denied, approved, and executed operations.
11. Loopback-only policy remains enforced.
12. Cloud endpoints remain rejected by default.
13. Alfred-facing requests remain bounded by policy.
14. Existing WP-0131 AI Services tests remain passing.
15. Existing work-package and production-readiness validation tests remain passing.

Use mocks for process execution. Tests must not launch actual third-party AI applications.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest tests/test_ai_services_control_plane.py -q
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0132 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If CLI names differ, use the existing canonical validation command names and document the mapping.

## Required Artifacts

Create:

```text
operations/ai_services/WP-0132_ai_services_execution_adapters_report.md
```

Create machine-readable companion:

```text
runtime/ai_services/WP-0132_ai_services_execution_adapters_report.json
```

The report must include:

- current git commit;
- files changed;
- execution adapter design;
- approval workflow design;
- dry-run behavior;
- process state path;
- audit log behavior;
- CLI commands added or changed;
- API behavior added or changed;
- TextGen model-load behavior;
- stop safety behavior;
- Alfred-facing boundary;
- tests run;
- validation commands run;
- known limitations;
- recommended next action.

## Required Outputs

- Process execution adapter abstraction.
- Mockable process runner.
- Approval workflow for service operations.
- Dry-run and real execution modes.
- Process state tracking.
- Conservative stop behavior.
- Approved TextGen model-load execution path.
- Updated audit logging.
- CLI/API support for approval and execution semantics.
- WP-0132 report Markdown and JSON.
- `collaboration/work_packages/completions/WP-0132_codex_done.json`.

## Completion Artifact

Create:

```text
collaboration/work_packages/completions/WP-0132_codex_done.json
```

It must include `work_package_id = WP-0132`, `codex_status = done`, summary, execution adapter paths, approval workflow paths, process state path, audit log path, CLI/API changes, TextGen model-load behavior, stop safety behavior, tests run, validation commands run, known limitations, recommended next action, `ready_for_ca_review = true`, and `merge_authority = ca_verified_auto_merge_allowed`.

## Acceptance Criteria

WP-0132 is complete when the Estate AI Services Control Plane can safely convert approved, manifest-declared service operations from planned actions into mock-tested local execution adapter calls, record process state, enforce Steward approval where required, support approved TextGen model-load execution semantics, preserve local-only and loopback-only policy, and keep Alfred bounded to governed service requests.

## Merge Class

Class A. Escalate only if implementation requires changing cloud model policy, public network exposure policy, resident API governance, memory/redaction policy, production-readiness semantics, Alfred authority boundaries, or third-party application installation/update/removal behavior.
