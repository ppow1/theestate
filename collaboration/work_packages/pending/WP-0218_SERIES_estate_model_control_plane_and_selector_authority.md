# SERIES TASK WP-0218 — Estate Model Control Plane and Selector Authority

## Codex Command

Read collaboration/work_packages/pending/WP-0218_SERIES_estate_model_control_plane_and_selector_authority.md and do exactly what it says.

## Mode

SERIES

## Mission

Correct the backward AI model architecture by moving model choice out of hardcoded resident adapters and into an Estate-governed model control plane.

The Estate must discover available local AI services and models, classify model capabilities, define Estate-level fallback/preferred models, define per-resident and per-worker model assignments, expose those choices through the Office of the Steward and CLI, and require authority gates for model/service use.

Adapters must execute selected policy. They must not decide policy.

## Problem Statement

Recent Alfred work exposed a structural flaw:

```text
Office / Alfred
  -> resident adapter
  -> adapter chooses provider/model
```

This is backwards.

The Estate now has:

- local Ollama models;
- AI Services Control Plane work;
- service discovery and rediscovery;
- Alfred resident chat;
- resident-specific model needs;
- image/vision model needs;
- worker/resident authority boundaries;
- Office UI surfaces;
- future Helen, Ingrid, Chief Architect, Chief Character Architect, and other resident roles.

Model selection can no longer live in hardcoded defaults such as `qwen3:8b` or `llama3.2-vision:11b` inside resident adapters or committed runtime config.

The correct architecture is:

```text
Office of the Steward
  -> Estate model registry and selector policy
  -> AI Services Control Plane provider/model discovery
  -> per-resident / per-worker assignment
  -> authority and approval gate
  -> adapter invocation
```

## Required Design Position

The Estate controls model selection.

Residents request capability.

Workers receive assigned model authority.

Adapters call the selected model.

Hardcoded model names may exist only as safe local defaults for initial bootstrapping, never as authoritative assignment policy.

## Preconditions

Before work begins:

1. Inspect WP-0131 AI Services Control Plane implementation and artifacts.
2. Inspect any WP-0132 or later AI services execution/approval work already merged.
3. Inspect current Alfred LLM adapter and diagnostic behavior.
4. Inspect current Office AI Services / Models UI surface.
5. Inspect resident authority and personnel/worker identity model.
6. Inspect existing runtime config paths for Alfred text and vision models.
7. Do not break WP-0217 Alfred timeout repair if it is in progress; this package is architectural model-selection governance, not the timeout fix.

If any precondition fails, stop and report the blocker.

## Scope

In scope:

1. Define an Estate model registry separate from, but sourced by, AI service discovery.
2. Discover models from available AI services, initially Ollama and TextGen where supported by existing manifests/control plane.
3. Classify models by capability, such as:
   - text;
   - code;
   - vision;
   - embedding;
   - image generation;
   - audio/transcription;
   - tool-capable;
   - unknown.
4. Define Estate-level fallback and preferred models.
5. Define per-resident model assignments.
6. Define per-worker model assignments.
7. Define per-capability model assignments.
8. Define model authority/permission gates per resident/worker/role.
9. Add Office of the Steward UI controls for viewing discovered models, current assignments, fallbacks, preferred models, and authority requirements.
10. Add CLI commands for rediscovery, listing models, viewing assignments, setting assignments, and validating assignments.
11. Add localhost-only API hooks only if consistent with existing Office/API conventions.
12. Update Alfred's model selection path to consume model-control-plane policy instead of choosing directly inside the adapter, while preserving safe fallback when the model plane is unavailable.
13. Ensure no vision request silently falls back to a text-only model.
14. Audit every model assignment change.
15. Add reports, tests, validation recipe, and completion receipt.

Out of scope:

- Fixing Alfred generation timeout behavior. That belongs to WP-0217.
- Installing new models.
- Downloading models.
- Moving model files.
- Cloud model providers unless already represented as disabled/disallowed inventory.
- Replacing the AI Services Control Plane.
- Granting residents unrestricted service authority.
- Automatic model switching without visible Steward policy.

## Required Architecture

Implement or document a canonical structure equivalent to:

```text
src/estate/model_control/
  __init__.py
  discovery.py
  registry.py
  assignments.py
  policy.py
  cli.py
  reports.py

runtime/model_control/
  registry.json
  assignments.json
  audit_log.jsonl
  diagnostics.json

operations/model_control/
  WP-0218_estate_model_control_plane_report.md
```

Use a more canonical existing repository layout if one exists. Document the choice.

## Required Model Registry

The model registry must record discovered models as facts, not preferences.

Minimum model record shape:

```json
{
  "model_id": "ollama:qwen3:8b",
  "provider": "ollama",
  "service_id": "ollama",
  "model_name": "qwen3:8b",
  "endpoint": "http://127.0.0.1:11434",
  "capabilities": ["text", "tools", "thinking"],
  "capability_confidence": "declared|inferred|unknown",
  "context_length": 40960,
  "size_bytes": 5225388164,
  "discovered_at": "ISO-8601",
  "available": true,
  "local_only": true,
  "cloud_allowed": false
}
```

The registry must not decide which resident uses the model.

## Required Assignment Model

Assignments must be separate from discovery.

Minimum assignment structure:

```json
{
  "estate_defaults": {
    "fallback_text_model": "ollama:qwen3:8b",
    "preferred_text_model": "ollama:qwen3:8b",
    "preferred_code_model": null,
    "preferred_vision_model": null
  },
  "residents": {
    "alfred": {
      "text": "ollama:qwen3:8b",
      "vision": null,
      "fallback_text": "estate_default"
    }
  },
  "workers": {
    "chief_architect_5": {
      "text": "estate_default",
      "code": null
    }
  }
}
```

The exact schema may differ if there is a better existing convention, but these concepts must be preserved.

## Required Authority Model

Model use must be governed.

At minimum, authority must express:

- which residents may use which model capabilities;
- which workers may use which model capabilities;
- whether model use requires Steward approval;
- whether a model is local-only or cloud-disallowed;
- whether a model may be used for vision, code, long-context reasoning, or general chat;
- whether a requested assignment is blocked because the model lacks the required capability.

Example policy decision:

```json
{
  "actor": "alfred",
  "requested_capability": "vision",
  "requested_model": "ollama:qwen3:8b",
  "decision": "denied",
  "reason": "Model is not classified as vision-capable"
}
```

## Required Office UI Layer

Add or update the Office of the Steward AI Services / Models workspace so the Steward can see and eventually control:

1. Discovered AI services.
2. Discovered models grouped by provider/service.
3. Detected model capabilities.
4. Estate fallback model.
5. Estate preferred text model.
6. Estate preferred vision model.
7. Alfred text and vision assignments.
8. Helen, Ingrid, Chief Architect, Chief Character Architect, and worker assignment readiness where records exist.
9. Authority status for each assignment.
10. Rediscovery action/status.
11. Last model discovery time.
12. Audit trail for assignment changes.

The UI may begin as a simple local control surface, but it must not require hand-editing JSON to see what model Alfred is supposed to use.

## Required CLI Commands

Add CLI commands equivalent to:

```bash
PYTHONPATH=src python -m estate.cli.main model-control rediscover --json
PYTHONPATH=src python -m estate.cli.main model-control list-models --json
PYTHONPATH=src python -m estate.cli.main model-control assignments --json
PYTHONPATH=src python -m estate.cli.main model-control set-default --capability text --model ollama:qwen3:8b --approved-by steward --json
PYTHONPATH=src python -m estate.cli.main model-control assign --actor alfred --capability text --model ollama:qwen3:8b --approved-by steward --json
PYTHONPATH=src python -m estate.cli.main model-control validate-assignments --json
```

Names may differ if repository CLI conventions require it. Document the mapping.

## Required Alfred Integration

Alfred must no longer treat adapter defaults as authoritative assignment policy.

When Alfred needs a model:

1. Query model-control assignment for resident `alfred` and capability `text` or `vision`.
2. Validate assignment against model registry and authority policy.
3. Invoke the adapter with the selected provider/model.
4. Report metadata showing the source of selection:

```json
{
  "selection_source": "model_control_assignment",
  "assigned_model": "ollama:qwen3:8b",
  "capability": "text",
  "policy_result": "allowed"
}
```

If model-control is unavailable, Alfred may use a safe bootstrap fallback, but must clearly label it:

```json
{
  "selection_source": "bootstrap_fallback",
  "warning": "Model control assignment unavailable"
}
```

## Required Reports

Create:

```text
operations/model_control/WP-0218_estate_model_control_plane_report.md
runtime/model_control/WP-0218_estate_model_control_plane_report.json
```

Report must include:

- root cause of the backwards architecture;
- final model-control paths;
- registry schema summary;
- assignment schema summary;
- authority policy summary;
- Office UI changes;
- CLI commands added;
- Alfred integration changes;
- tests run;
- validation commands run;
- known limitations;
- recommended next action.

## Required Tests

Add or update tests for:

1. Model discovery from mocked Ollama service data.
2. Model registry generation.
3. Capability classification.
4. Unknown capability handling.
5. Estate fallback/preferred assignment storage.
6. Per-resident assignment storage.
7. Per-worker assignment storage.
8. Policy denial when a text-only model is assigned for vision.
9. Policy denial when an actor lacks authority to use a model/capability.
10. Audit log write on assignment changes.
11. CLI model rediscovery/list/assignment commands.
12. Office UI renders model selector workspace content.
13. Alfred consumes assigned model selection rather than hardcoded adapter default.
14. Existing Alfred diagnostics and chat tests remain passing.

Use mocked provider data. Do not require real Ollama in CI/Codex.

## Required Validation

Run or document equivalent:

```bash
PYTHONPATH=src pytest tests/test_model_control.py tests/test_resident_interaction.py tests/test_steward_command_center.py -q
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0218 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Add a WP-0218 validation recipe if missing.

## Completion Artifact

Create:

```text
collaboration/work_packages/completions/WP-0218_codex_done.json
```

It must include:

```json
{
  "work_package_id": "WP-0218",
  "codex_status": "done",
  "completed_at": "...",
  "branch": "...",
  "summary": "...",
  "root_cause": "Model selection lived inside adapters/resident defaults rather than an Estate-governed model-control layer.",
  "files_changed": [],
  "tests_run": [],
  "validation_commands_run": [],
  "known_limitations": [],
  "ready_for_ca_review": true,
  "merge_authority": "ca_verified_auto_merge_allowed",
  "pull_request_url_or_not_applicable_reason": "..."
}
```

## Acceptance Criteria

WP-0218 is complete when model discovery, model selection, fallback/preferred model policy, per-resident/per-worker assignments, capability validation, assignment authority, CLI controls, Office UI visibility, and Alfred model selection all flow through an Estate model-control layer rather than hardcoded adapter decisions.

## Merge Class

Class A. Escalate only if implementation requires changing Steward authority, enabling cloud providers, granting residents unrestricted service authority, moving model files, or replacing the AI Services Control Plane rather than integrating with it.
