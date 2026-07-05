# SERIES TASK WP-0131 — AI Services Control Plane

## Codex Command

Read collaboration/work_packages/pending/WP-0131_SERIES_ai_services_control_plane.md and do exactly what it says.

## Mode

SERIES

## Mission

Create an Estate-compatible local AI services control plane that lets the Estate describe, rediscover, inspect, and govern local AI services without hardcoding one-off launcher scripts.

The control plane must support Alfred and future Estate workers through approved command-line hooks and localhost-only API hooks for local service status, approved startup requests, approved shutdown requests, and approved model-load requests.

## Problem Statement

The Steward is running several local AI applications under `A:\AI`, including Open WebUI, Ollama, TextGen, ComfyUI, and SillyTavern. These applications have separate launchers, ports, configuration styles, and model locations. Manual startup produces too many terminal windows, and ad hoc launcher scripts are brittle.

The Estate needs a governed local service-control layer so Alfred can eventually inspect service state and request model loads on demand after Steward authority is granted. This must be implemented as a rediscoverable service registry/control subsystem, not as a monolithic script.

## Architectural Boundary

`A:\AI` is infrastructure.

`A:\theestate` is the institution.

This work package defines Estate-controlled service metadata and control behavior while describing local infrastructure applications that physically live under `A:\AI`.

The implementation must not assume that all models already live in one canonical directory. It must discover and record current model locations as facts, then allow service manifests to declare which locations each service uses.

## Preconditions

1. Confirm repository root and existing Estate conventions before adding new structure.
2. Inspect existing collaboration/work package conventions and validation tooling.
3. Inspect any existing runtime, operations, scripts, residents, governance, service, or local infrastructure conventions before creating new ones.
4. Confirm WP-0130 or equivalent local-vision work does not already implement service management. WP-0130 explicitly left service launching/managing such as ComfyUI or SillyTavern out of scope.
5. Do not move model files.
6. Do not install, update, or remove third-party AI applications.
7. Do not expose any control API outside loopback.
8. Do not add cloud API behavior.

If any precondition fails, stop and report the exact blocker.

## Scope

In scope:

1. Define an Estate AI Services subsystem structure.
2. Define rediscoverable service implementation manifests.
3. Provide a discovery mechanism that scans service implementation manifests and rebuilds a current registry.
4. Record current runtime state separately from static manifests.
5. Provide command-line hooks for service status, rediscover, approved start, approved stop, and approved model-load requests.
6. Provide a localhost-only HTTP API surface for the same approved operations if consistent with existing Estate API conventions.
7. Provide explicit Alfred-facing command/API hooks without granting Alfred unrestricted host access.
8. Provide policy gates for operations that require Steward approval.
9. Provide audit logs for every requested service operation.
10. Seed manifests for known local services: Ollama, Open WebUI, TextGen, ComfyUI, and SillyTavern.
11. Support TextGen model-load requests through declared command templates.
12. Support Ollama model availability/status discovery through declared command/API templates.
13. Treat service model directories as manifest-declared facts, not global assumptions.
14. Add tests for manifest discovery, registry generation, policy gating, loopback binding, logging, and model-load request planning.
15. Add validation recipe and completion receipt.

Out of scope:

- Moving or deduplicating model files.
- Declaring a canonical model directory for all services.
- Installing models automatically.
- Installing, updating, or removing local AI applications.
- Cloud APIs.
- Public network exposure.
- Replacing Open WebUI, Ollama, TextGen, ComfyUI, or SillyTavern.
- Full desktop GUI launcher. A GUI may come later and should consume the control plane.
- Granting Alfred unrestricted host command access.
- Stop/update/remove operations without explicit governance and approval semantics.

## Required Design

Create or use an existing canonical location for Estate service-control metadata. If no canonical location exists, create a structure equivalent to:

```text
src/estate/ai_services/
  __init__.py
  discovery.py
  manifest.py
  registry.py
  state.py
  policy.py
  control.py
  api.py
  cli.py
```

Create runtime/operations artifacts equivalent to:

```text
runtime/ai_services/
  registry.json
  state.json
  audit_log.jsonl
  implementations/

operations/ai_services/
  WP-0131_ai_services_control_plane_report.md
```

If the repository already has a more canonical runtime/operations layout, use it instead and document the choice.

## Service Implementation Manifests

Define a machine-readable manifest schema for rediscoverable local services. The schema must support at least:

- `service_id`
- `display_name`
- `service_type`
- `local_only`
- `host_policy`
- `default_endpoint`
- `ports`
- application paths
- status check definition
- approved start request definition
- approved stop request definition where supported
- model operation definition where supported
- approval requirements

Discovery must scan manifests rather than hardcoded service lists.

## Required Seed Service Manifests

Seed service manifests for these known local services. Use discovered and configurable paths rather than hardcoded assumptions where possible.

### Ollama

Known local endpoint:

```text
http://127.0.0.1:11434
```

Expected operations:

- status
- list models
- list running models, if supported locally
- start request where safe and available
- model availability check

### Open WebUI

Known local endpoint:

```text
http://127.0.0.1:8080
```

Known local installation pattern:

```text
A:\AI\OpenWebUI
```

Expected operations:

- status
- start request
- stop request where safe
- no model loading; it delegates to backends

### TextGen

Known local endpoint:

```text
http://127.0.0.1:5000/v1
```

Known local installation pattern:

```text
A:\AI\TextGen\textgen-4.9
```

Known launcher:

```text
A:\AI\TextGen\textgen-4.9\textgen.bat
```

Known model folder observed locally:

```text
A:\AI\TextGen\textgen-4.9\user_data\models
```

Observed working approved model-load command pattern:

```powershell
Set-Location A:\AI\TextGen\textgen-4.9
.\textgen.bat --nowebui --listen --model "Qwen3-8B-Q6_K.gguf" --loader llama.cpp
```

Expected operations:

- status through `/v1/models`
- list currently loaded model
- load model by approved request
- report when no model is loaded
- model directory inventory

### ComfyUI

Known local installation pattern:

```text
A:\AI\ComfyUI
```

Expected operations:

- status
- start request if a safe launcher is detected
- no blind assumptions about launcher name
- no workflow execution in this work package

### SillyTavern

Known local installation pattern:

```text
A:\AI\SillyTavern
```

Expected operations:

- status
- discover safe launcher candidates
- do not run arbitrary `Start.bat` without manifest confirmation, because an earlier naive launcher attempt opened the wrong target
- no character/session automation in this work package

## Rediscovery Requirement

Discovery must scan implementation manifests, not hardcoded service lists.

A canonical equivalent should exist:

```text
runtime/ai_services/implementations/*/service.manifest.json
```

or an existing canonical Estate location if found.

Discovery must:

1. Find all implementation manifests.
2. Validate schema and required fields.
3. Reject or quarantine unsafe manifests.
4. Rebuild `registry.json` from valid manifests.
5. Preserve dynamic runtime state separately.
6. Produce a human-readable discovery report.
7. Log rediscovery events.

## Policy Requirements

All control actions must pass a policy gate.

Minimum policies:

1. Control API binds only to `127.0.0.1`.
2. Cloud endpoints are rejected unless an explicit future policy permits them.
3. Model loads require approved authority.
4. Unknown operations are rejected.
5. Stop/update/remove actions are disallowed unless specifically modeled and approved.
6. Service manifests may not request public network exposure by default.
7. Alfred may request only allowed operations through the control plane.
8. Alfred must not receive unrestricted host command access.

## Alfred Integration Requirement

Provide an Alfred-facing contract, but do not require Alfred to implement full autonomous service management in this work package.

The contract should allow Alfred, after Steward authority is granted, to request equivalent behavior to:

```text
GET  /ai-services/status
GET  /ai-services/services
GET  /ai-services/services/{service_id}
POST /ai-services/services/{service_id}/start
POST /ai-services/services/{service_id}/stop
POST /ai-services/services/{service_id}/models/load
POST /ai-services/rediscover
```

Equivalent CLI commands should also exist, for example:

```bash
PYTHONPATH=src python -m estate.cli.main ai-services status
PYTHONPATH=src python -m estate.cli.main ai-services rediscover
PYTHONPATH=src python -m estate.cli.main ai-services start --service textgen --approved-by steward
PYTHONPATH=src python -m estate.cli.main ai-services load-model --service textgen --model Qwen3-8B-Q6_K.gguf --approved-by steward
```

Command names may differ if required by existing CLI conventions, but the behavior must be equivalent and documented.

## Audit Log Requirements

Every service-control request must append a structured local audit record with at least:

```json
{
  "timestamp": "...",
  "actor": "alfred|steward|codex|system",
  "operation": "load_model",
  "service_id": "textgen",
  "requested_model": "Qwen3-8B-Q6_K.gguf",
  "authority": "steward_approved",
  "policy_result": "allowed|denied",
  "result": "success|failed|planned_only",
  "details": {}
}
```

The log must be local. Do not emit service-control audit events to cloud services.

## Model Location Requirement

The control plane must not decide that all models belong in one place.

It must instead record locations as facts from manifests and discovery, such as:

```text
A:\AI\Models
A:\AI\TextGen\textgen-4.9\user_data\models
Ollama-managed model store
ComfyUI model directories
```

A later work package may evaluate model storage consolidation. This work package must not move model files or create symlinks.

## Required Tests

Add or update tests for:

1. Service manifest schema validation.
2. Rediscovery scans implementation manifests.
3. Registry generation from manifests.
4. Invalid or unsafe manifest rejection.
5. Loopback-only API binding policy.
6. Cloud endpoint rejection by default.
7. Alfred-facing operation policy gates.
8. TextGen model-load request planning.
9. No model movement during discovery.
10. Audit log write for allowed operation.
11. Audit log write for denied operation.
12. CLI status and rediscover commands.
13. API status endpoint, if the Estate has a resident/local API test harness.
14. Existing production-readiness and work-package validation tests remain passing.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0131 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If the CLI names differ, use the existing canonical validation command names and document the mapping.

## Required Artifacts

Create:

```text
operations/ai_services/WP-0131_ai_services_control_plane_report.md
```

Create machine-readable companion:

```text
runtime/ai_services/WP-0131_ai_services_control_plane_report.json
```

The report must include:

- current git commit;
- final subsystem paths;
- manifest schema summary;
- seeded service manifests;
- rediscovery behavior;
- registry path;
- state path;
- audit log path;
- CLI commands added;
- API endpoints added;
- policy gates;
- Alfred-facing contract;
- model-location handling;
- tests run;
- validation commands run;
- known limitations;
- recommended next action.

## Required Outputs

- AI service manifest schema.
- Rediscoverable implementation manifest layout.
- Registry generation from manifests.
- Runtime state separation from static manifests.
- Local audit logging.
- CLI hooks for status, rediscover, approved start, approved stop, and approved load-model behavior.
- Localhost-only API hooks if consistent with existing Estate API conventions.
- Seed manifests for Ollama, Open WebUI, TextGen, ComfyUI, and SillyTavern.
- WP-0131 report Markdown and JSON.
- WP-0131 validation recipe and runtime validation artifacts.
- `collaboration/work_packages/completions/WP-0131_codex_done.json`.

## Completion Artifact

Create:

```text
collaboration/work_packages/completions/WP-0131_codex_done.json
```

It must include `work_package_id = WP-0131`, `codex_status = done`, summary, subsystem paths, seeded services, registry path, state path, audit log path, CLI/API hooks, policy gates, tests run, validation commands run, known limitations, recommended next action, `ready_for_ca_review = true`, and `merge_authority = ca_verified_auto_merge_allowed`.

## Acceptance Criteria

WP-0131 is complete when the Estate has a rediscoverable local AI services control plane that can describe known local AI services, rebuild a service registry from manifests, expose governed local command/API hooks, record service-control audit events, support approved TextGen model-load requests without assuming model storage consolidation, and preserve the local-first/no-cloud/no-public-exposure boundary.

## Merge Class

Class A. Escalate only if implementation requires changing cloud model policy, server exposure/security policy, resident API governance, memory/redaction policy, production-readiness semantics, or Alfred authority boundaries.
