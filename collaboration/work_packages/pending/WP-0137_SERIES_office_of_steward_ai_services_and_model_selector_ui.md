# SERIES TASK WP-0137 - Office of the Steward AI Services and Model Selector UI

## Codex Command

Read collaboration/work_packages/pending/WP-0137_SERIES_office_of_steward_ai_services_and_model_selector_ui.md and do exactly what it says.

## Mode

SERIES

## Mission

Add an Office of the Steward UI/control layer above Alfred chat and above the raw AI Services Control Plane so the Steward can see, select, approve, and govern local AI services and models as Estate resources.

This is not merely a dropdown for which model Alfred uses. It is a governed Services and Model Selector layer for the Estate's local AI infrastructure.

## Context

WP-0131 created the lower-level AI Services Control Plane: service manifests, rediscovery, registry/state/audit files, CLI hooks, localhost API hooks, and policy gates.

WP-0132 added execution adapters and approval semantics.

WP-0133 through WP-0136 repaired health verification, Windows batch launcher behavior, interruption cleanup, and per-attempt diagnostics. A governed TextGen launch was validated end to end.

The missing layer is a Steward-facing UI that exposes those capabilities without requiring the Steward to edit JSON files or run CLI commands manually.

## Architectural Position

The UI must sit here:

```text
Office of the Steward
  AI Services / Models control layer
    Alfred chat and resident interactions
    AI Services Control Plane
      local services under A:\AI
```

The Office of the Steward owns authority and configuration. Alfred may display his current assignment and request actions, but model/service authority belongs to the Steward-facing layer.

## Required UI Concept

Create or extend a Steward UI area equivalent to:

```text
Office of the Steward
  AI Services / Models
    Services
    Models
    Worker assignments
    Authority / approvals
    Rediscovery / audit
```

Use the existing Office of the Steward, Steward Command Center, Operations Center, or nearest canonical UI surface if one already exists. Do not invent a parallel UI framework if an existing Steward surface can absorb this.

## In Scope

1. Add a Steward-facing AI Services / Models panel or equivalent UI surface.
2. Display discovered services from the AI Services registry.
3. Display current service status from AI Services state.
4. Display service health and last operation.
5. Display per-attempt log path or link/reference when available.
6. Display discovered or configured model inventory where available.
7. Support rediscovery action.
8. Support status refresh action.
9. Support approved service start/stop request flow where existing control-plane operations allow it.
10. Support approved TextGen load-model request flow.
11. Add Estate-level model preference fields or artifacts for:
    - Estate fallback text model;
    - Estate preferred text model;
    - Estate preferred vision model;
    - Alfred assigned model;
    - Helen assigned model;
    - worker/resident-specific model assignments.
12. Add worker-specific model/service authority display and editing path, bounded by existing authority policy.
13. Display pending approvals from AI Services approvals.
14. Allow Steward approve/deny decisions through governed hooks, not direct JSON edits.
15. Display AI Services audit log tail and recent service events.
16. Preserve loopback-only, local-first, no-cloud-by-default behavior.
17. Add CLI/API support only where needed to back the UI cleanly.
18. Add tests and validation artifacts.

## Out of Scope

- Replacing Alfred chat.
- Burying the selector inside Alfred chat as Alfred-only settings.
- Granting Alfred unrestricted service or model authority.
- Moving model files.
- Consolidating model storage.
- Installing models automatically.
- Installing, updating, or removing third-party services.
- Public network exposure.
- Cloud model behavior unless a later explicit policy permits it.
- Full desktop native app launcher.

## Required Behavior

### Services View

The UI must show at least:

- Ollama;
- TextGen;
- ComfyUI;
- Open WebUI;
- SillyTavern.

For each service, show equivalent data:

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
- current or recent log reference.

### Models View

The UI must show discovered/configured model information from available sources, including at least:

- TextGen manifest model directory inventory where supported;
- Ollama model inventory where available;
- service-specific model locations declared in manifests;
- model capability classification when known or configurable, such as text, vision, embedding, image, audio, or workflow support.

If classification is not yet available, create a minimal conservative metadata structure and mark unknowns clearly.

### Estate Defaults

Add or expose a governed model preference artifact for Estate defaults:

```text
estate_fallback_text_model
estate_preferred_text_model
estate_preferred_vision_model
```

These defaults must reference known/discovered models or be explicitly marked unresolved.

### Worker/Resident Assignments

Add or expose assignments for residents/workers, including at least:

```text
Alfred assigned model
Helen assigned model
Chief Architect model assignment, if applicable
Codex worker default model, if applicable
future worker-specific assignments
```

Assignments should include:

- model id;
- backing service;
- allowed operations;
- approval requirement;
- reason/comment;
- last updated timestamp;
- updated by.

### Authority and Approval

The UI must not bypass the control-plane policy gates.

The Steward may approve or deny pending service/model requests. Alfred may request actions but must not approve his own authority expansion unless existing Estate policy already allows that.

### Audit and Rediscovery

The UI must support:

- rediscover services;
- refresh status;
- show recent AI Services audit events;
- show pending approvals;
- show last successful/failed launch attempts.

## Required Data/Artifacts

Use existing canonical runtime/operations directories where possible. If no canonical artifact exists, create documented equivalents such as:

```text
runtime/ai_services/model_preferences.json
runtime/ai_services/model_assignments.json
operations/ai_services/WP-0137_office_of_steward_ai_services_model_selector_ui_report.md
runtime/ai_services/WP-0137_office_of_steward_ai_services_model_selector_ui_report.json
```

Do not store secrets in these files.

## CLI/API Requirements

Add or extend CLI/API hooks only as needed to back the UI. Equivalent behavior should exist for:

```text
ai-services models
ai-services model-preferences
ai-services set-model-preference
ai-services assignments
ai-services set-assignment
ai-services approvals
ai-services approve
ai-services deny
```

Names may follow existing Estate conventions, but behavior must be documented.

## Tests

Add tests for:

1. Steward UI data model builds from AI Services registry/state.
2. Services list includes the five seeded local services.
3. Model inventory exposes TextGen and Ollama sources when available or marks unavailable clearly.
4. Estate model preferences validate references or mark unresolved.
5. Worker model assignments are persisted and read back.
6. Alfred cannot approve his own service/model authority expansion through this layer.
7. Steward approval/denial updates governed approval records.
8. Rediscovery/status refresh hooks are represented in the UI data model.
9. Audit tail is exposed without leaking secrets.
10. Existing AI Services control-plane tests remain passing.
11. Work-package and production-readiness validation tests remain passing.

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src pytest -q tests/test_ai_services_control_plane.py
PYTHONPATH=src pytest -q tests/test_work_package_validation.py tests/test_production_readiness_validation.py
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

If a dedicated WP-0137 validation recipe is available, run it. If not, document the missing recipe explicitly.

## Required Artifacts

Create:

```text
operations/ai_services/WP-0137_office_of_steward_ai_services_model_selector_ui_report.md
runtime/ai_services/WP-0137_office_of_steward_ai_services_model_selector_ui_report.json
collaboration/work_packages/completions/WP-0137_codex_done.json
```

The report must include:

- final UI/control surface path;
- service data displayed;
- model data displayed;
- model preference artifacts;
- worker assignment artifacts;
- approval behavior;
- audit/rediscovery behavior;
- CLI/API changes;
- tests run;
- validation results;
- known limitations;
- recommended next action.

## Acceptance Criteria

WP-0137 is complete when the Office of the Steward has a Steward-facing AI Services and Model Selector layer that exposes discovered local services, discovered/configured models, Estate defaults, worker/resident model assignments, approval gates, rediscovery, and audit visibility without requiring manual JSON editing and without bypassing the AI Services Control Plane.

## Merge Class

Class A. Escalate only if implementation requires changing approval authority, public network exposure, cloud model policy, resident authority boundaries, production-readiness semantics, or third-party installation/update/removal behavior.
