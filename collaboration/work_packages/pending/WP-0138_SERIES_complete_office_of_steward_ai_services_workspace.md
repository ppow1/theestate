# SERIES TASK WP-0138 - Complete Office of the Steward AI Services Workspace

## Codex Command

Read collaboration/work_packages/pending/WP-0138_SERIES_complete_office_of_steward_ai_services_workspace.md and do exactly what it says.

## Mode

SERIES

## Mission

Complete the Office of the Steward AI Services / Models workspace so the Steward can operate the Estate's local AI infrastructure from the Command Center without manually editing JSON files or relying on raw CLI commands for normal inspection.

This work builds on WP-0131 through WP-0137.

Do not create a new AI Services Control Plane. Use the existing registry, state, audit, discovery, approval, execution, model preference, and model assignment infrastructure.

## Architectural Principle

The Office of the Steward is the authority surface.

Alfred, Helen, Chief Architects, Codex workers, and future residents consume AI services according to assignment and authority.

Alfred chat may display Alfred's current model, but the governed service/model selection layer belongs to the Office of the Steward.

## Existing Infrastructure To Reuse

Reuse and strengthen existing artifacts and code:

- `runtime/ai_services/registry.json`
- `runtime/ai_services/state.json`
- `runtime/ai_services/model_preferences.json`
- `runtime/ai_services/model_assignments.json`
- `runtime/ai_services/audit_log.jsonl`
- `runtime/ai_services/approvals.json`
- `src/estate/ai_services/steward_model_selector.py`
- `src/estate/cli/main.py`
- `src/estate/core/steward_command_center.py`
- `runtime/steward/command_center.html`

If an existing Steward Command Center generator can absorb the work, use it. Do not invent a parallel UI framework.

## Required Workspace Structure

The Office of the Steward shall expose a first-class workspace equivalent to:

```text
Office of the Steward
  AI Services / Models
    Dashboard
    Services
    Models
    Worker Assignments
    Authority / Approvals
    Rediscovery / Audit
```

The current AI Services / Models navigation item must lead to visible operational content, not only a placeholder.

## Required Sections

### 1. Dashboard

Show a summary of:

- discovered services count;
- running services count;
- unhealthy services count;
- pending approvals count;
- known installed models count;
- active Estate default model assignments;
- recent AI Services audit entries.

### 2. Services

Display every discovered service from the AI Services registry, including at minimum:

- Ollama;
- Text Generation WebUI;
- ComfyUI;
- Open WebUI;
- SillyTavern.

For each service display:

- service id;
- display name;
- service type;
- endpoint;
- host policy;
- ports;
- current state;
- health status;
- last operation;
- available operations;
- approval requirements;
- current or recent log reference;
- manifest path;
- model locations.

### 3. Model Inventory

Display discovered/configured models grouped by backing service.

The inventory must distinguish these concepts:

- installed;
- currently loaded;
- preferred;
- assigned;
- default;
- unavailable;
- unresolved.

Do not conflate loaded model with installed model inventory.

### 3A. Filesystem Model Discovery

The Steward workspace shall enumerate every model physically installed for each supported service where a model location is declared.

For Text Generation WebUI, discovery shall enumerate the configured model directory specified by the service manifest, currently equivalent to:

```text
A:\AI\TextGen\textgen-4.9\user_data\models
```

Supported discoveries include:

- GGUF model files;
- HuggingFace-style model directories;
- service-supported model layouts that can be identified safely;
- directories that appear to represent model repositories.

The inventory must not be limited to the currently loaded model.

Example installed TextGen inventory should include all available entries such as:

```text
Qwen3-8B-Q6_K.gguf
Meta-Llama-3.1-8B-Instruct-Q5_K_M.gguf
magnum-v4-72b-Q4_K_M.gguf
Q5KM-Charcard-RP-1b_Uncensored.gguf
qwen3-32b-vl-instruct-polaris-hi16-...
Weiwei22_WaifuChat-8b
RichardErkhov_Tann-dev_...
```

The UI shall mark the currently loaded model separately from installed models.

### 4. Estate Model Preferences

Expose and render governed Estate defaults from `model_preferences.json` or an improved compatible artifact:

- Estate fallback text model;
- Estate preferred text model;
- Estate preferred vision model;
- Estate preferred embedding model;
- Estate preferred coding model;
- Estate preferred speech model.

Preferences must reference known/discovered models or be clearly marked unresolved.

### 5. Worker / Resident Assignments

Display resident and worker assignments from `model_assignments.json` or an improved compatible artifact.

Include at minimum:

- Steward;
- Alfred;
- Helen;
- Chief Architects where represented;
- Codex workers where represented;
- future residents/workers discovered by existing Estate personnel or runtime artifacts.

Each assignment should show:

- assigned model;
- fallback model;
- backing service;
- allowed services;
- allowed operations;
- approval requirement;
- reason/comment;
- last updated timestamp;
- updated by.

### 6. Authority / Approvals

Render approval and authority state from existing AI Services approval/policy artifacts.

Show:

- pending approvals;
- approved requests;
- denied requests;
- start service approval requirements;
- stop service approval requirements;
- load model approval requirements;
- resident/worker-specific permission state where available.

The UI must not allow Alfred or any other resident to approve their own service/model authority expansion unless existing governance explicitly permits it.

### 7. Operational Controls

Add local UI controls or clearly documented command hooks for:

- Rediscover Services;
- Refresh Status;
- Refresh Models;
- View Registry;
- View State;
- View Audit;
- View Approvals.

These controls shall call existing Estate behavior or minimal supporting hooks. Do not duplicate the control plane.

If the generated static HTML cannot safely execute commands directly, render exact local commands for the Steward to copy and run.

### 8. Health

Display service health including:

- running/stopped/unhealthy/interrupted/health_failed;
- PID if known;
- endpoint;
- port;
- last health result;
- last startup time;
- startup failures;
- process exit code when available;
- latest per-attempt log path when available.

### 9. Audit

Display recent entries from `runtime/ai_services/audit_log.jsonl` newest first.

Audit display must avoid leaking secrets. If no audit entries exist, show that state clearly.

### 10. Service Details

Selecting or expanding a service shall display:

- manifest path;
- paths;
- ports;
- operations;
- approval requirements;
- launcher;
- working directory;
- model locations;
- host policy;
- local-only state.

### 11. Worker Permissions

Display per-worker permissions in a way the Steward can understand.

Example:

```text
Alfred
  TextGen: allowed with Steward approval for load_model
  Ollama: allowed with policy gate
  ComfyUI: not yet approved

Helen
  Ollama: allowed
  TextGen: not assigned
```

Use existing governance and assignment artifacts. Do not invent a disconnected permission registry if an existing artifact can be extended safely.

## CLI / API Requirements

Add only minimal supporting commands needed to back the UI cleanly. Prefer existing command conventions.

Equivalent capabilities should exist or be documented for:

- listing Steward AI Services model-selector data;
- refreshing model inventory;
- listing model preferences;
- setting model preferences;
- listing model assignments;
- setting model assignments;
- listing approvals;
- approving or denying requests where existing approval machinery supports it.

Do not bypass approval policy.

## UI Requirements

- Remain entirely local.
- Do not add cloud calls.
- Do not introduce a JavaScript framework.
- Continue using the generated Steward HTML architecture unless an existing Estate UI convention says otherwise.
- Keep the UI readable in a browser without a build step.
- Missing artifacts should render as missing/unavailable, not crash generation.

## Refresh Behavior

The Refresh Models action shall perform filesystem model discovery for supported model locations.

The Rediscover Services action shall update or instruct the Steward how to update:

- service registry;
- service capabilities;
- installed model inventory;
- relevant health/status artifacts.

Manual JSON editing must not be required for normal refresh.

## Tests

Add or update tests proving:

1. Steward UI data model builds from AI Services registry/state.
2. Services list includes the five seeded local services.
3. Model inventory includes TextGen model directory entries when provided by a test fixture.
4. Multiple GGUF files are discovered.
5. Model directories are discovered.
6. Currently loaded model is distinguished from installed models.
7. Installed models not currently loaded remain visible.
8. Estate model preferences validate references or mark unresolved.
9. Worker model assignments are persisted and read back.
10. Alfred cannot approve his own service/model authority expansion through this layer.
11. Steward approval/denial updates governed approval records where supported.
12. Rediscovery/status refresh hooks are represented in the UI data model.
13. Audit tail is exposed without leaking secrets.
14. Existing AI Services control-plane tests remain passing.
15. Steward Command Center generation remains passing.
16. Work-package and production-readiness validation tests remain passing.

Use fixtures and mocks. Do not launch real third-party AI services in tests.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest -q tests/test_ai_services_control_plane.py
PYTHONPATH=src pytest -q tests/test_ai_services_steward_model_selector.py
PYTHONPATH=src pytest -q tests/test_work_package_validation.py tests/test_production_readiness_validation.py
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If a dedicated WP-0138 validation recipe is available, run it. If no recipe exists, document that explicitly.

## Required Artifacts

Create:

```text
operations/ai_services/WP-0138_complete_office_of_steward_ai_services_workspace_report.md
runtime/ai_services/WP-0138_complete_office_of_steward_ai_services_workspace_report.json
collaboration/work_packages/completions/WP-0138_codex_done.json
```

The report must include:

- final Steward workspace path;
- service data rendered;
- model data rendered;
- filesystem model discovery behavior;
- preference behavior;
- assignment behavior;
- approval behavior;
- audit/rediscovery behavior;
- CLI/API changes;
- tests run;
- validation results;
- known limitations;
- recommended next action.

## Acceptance Criteria

WP-0138 is complete when the Office of the Steward has a visible AI Services / Models workspace that exposes discovered services, installed models, loaded models, Estate defaults, worker/resident model assignments, approval gates, rediscovery/status/audit visibility, and filesystem model discovery without requiring manual JSON editing and without bypassing the AI Services Control Plane.

## Merge Class

Class A. Escalate only if implementation requires changing approval authority, public network exposure, cloud model policy, resident authority boundaries, production-readiness semantics, or third-party installation/update/removal behavior.
