# WP-4001 — Estate Multi-Resident Chat Gateway and Helen Activation

Status: Pending
Owner: Resident Runtime Implementation Stream
Originating Office: Character Architecture
Execution Target: Codex
Priority: Immediate

## Objective

Generalize the current Alfred-centered resident chat path into one governed multi-resident gateway, then bring Helen online through it so the Steward can talk to Helen before Helen is used to hire and onboard Grace.

Do not build a second chat system. Reuse the existing resident interaction, authority, memory, attachment, model-control, and Office surfaces.

## Read First

- `src/estate/core/resident_interaction.py`
- `src/estate/core/resident_authority.py`
- `src/estate/core/steward_command_center.py`
- `src/estate/model_control/assignments.py`
- `src/estate/model_control/policy.py`
- `src/estate/model_control/registry.py`
- `tests/test_resident_interaction.py`
- `tests/test_steward_command_center.py`
- `docs/residents/helen/Helen_Resident_Profile_v0_2.md`
- `docs/residents/helen/Helen_Resident_Validation_v0_2.md`
- `docs/residents/helen/Helen_Hiring_Onboarding_Workflow_v0_1.md`
- `docs/residents/helen/Helen_Local_Standup_Runbook_v0_1.md`
- `docs/residents/helen/Helen_Standup_Readiness_Matrix_v0_1.md`
- `docs/residents/helen/runtime/Helen_Workforce_Development_Runtime_Integration_v0_2.md`
- `docs/residents/helen/platform-exports/textgen-4_9-helen-v0_2.yaml`
- `src/estate/core/helen_workforce.py`
- `src/estate/cli/helen_workforce.py`
- `tests/test_helen_workforce.py`
- `tests/test_helen_workforce_cli.py`
- `tests/character_architecture/test_helen_resident_package.py`
- `docs/residents/alfred/platform-exports/textgen-4_9-alfred-v0_1.yaml`
- `docs/residents/grace/Grace_Resident_Profile_v0_1.md`

## Current Problem

Generic resident endpoints exist, but the effective local-LLM path is still Alfred-specific. Alfred-specific model bootstrap, diagnostics, prompt construction, request classification, and fallback behavior remain embedded in the shared path, while non-Alfred residents receive generic responses. Open WebUI also has no Estate OpenAI-compatible resident endpoint.

Helen is routed but not fully instantiated.

## Architectural Invariants

1. The Estate owns resident identity, authority, memory, continuity, and model routing.
2. Open WebUI is only a front end.
3. Alfred must remain Alfred; Helen must not inherit Alfred's prompt, office, authority, diagnostics, or model state.
4. Helen remains Human Resources and Workforce Development.
5. Helen may conduct approved hiring and onboarding for authorized roles, but may not create offices, grant authority, or bypass Steward-reserved appointments.
6. Ingrid retains privacy, classification, connector, and protected-source authority.
7. Private journals and sensitive workforce details must not become unrestricted chat context.
8. Chat must not execute privileged actions.
9. The runtime never becomes the resident, and the resident never becomes the runtime.
10. Grace remains a resident candidate and must not be activated here.
11. Preserve existing Alfred and Helen behavior unless a failing test proves a necessary shared-framework repair.
12. Do not inspect or use protected private local character material.

## Required Implementation

### 1. Resident-Specific Prompt Construction

Replace the effective Alfred-only prompt path with a resident-aware prompt constructor.

Required behavior:

- Alfred receives Alfred's canonical identity and boundaries.
- Helen receives Helen's canonical identity, HR/workforce mission, cognitive-health and continuity responsibilities, institutional-learning behavior, and Grace/Alfred/Ingrid/Engineering/Steward boundaries.
- Unknown residents receive an explicit limited generic prompt, never Alfred's prompt.
- Include resident identity, office, role, authority result, allowed capabilities, bounded Estate context, recent active session turns, provider/model metadata, and the current Steward message.
- Do not inject unrestricted private journals or protected-source text.

Preferred shape:

```text
resident_prompt(resident, message, surface, authority, context, llm_metadata)
```

### 2. Resident-Specific Model Selection and Diagnostics

- Resolve model-control assignment using the selected resident ID.
- Preserve explicit local fallback when assignment is unavailable.
- Do not use `ESTATE_ALFRED_OLLAMA_MODEL` as the universal fallback.
- Support resident-specific overrides if useful.
- Write diagnostics to `runtime/residents/<resident>/llm_diagnostics.json`.
- Keep Alfred's existing diagnostic path compatible if other code depends on it.
- Report resident, provider, model, assignment source, fallback state, failure reason, and recovery hint truthfully.

### 3. Real Helen Chat Path

When a local provider is available, Helen must:

- identify as Helen;
- identify Human Resources and Workforce Development;
- understand staffing, onboarding, workforce readiness, cognitive health, Character Continuity, and institutional learning;
- distinguish worker failure from institutional failure;
- preserve Grace, Alfred, Ingrid, Engineering, Traffic Controller, and Steward boundaries;
- avoid diagnosis from insufficient evidence;
- protect private journals;
- avoid claiming unavailable live access;
- never create offices or appoint Grace;
- remain warm, observant, discreet, capable, and natural under light workplace banter.

### 4. OpenAI-Compatible Local Resident Gateway

Implement:

```text
GET  /v1/models
POST /v1/chat/completions
```

Expose at least:

```text
estate/alfred
estate/helen
```

Requirements:

- standard non-streaming OpenAI-style request and response envelopes;
- map `estate/<resident>` to the shared Estate resident framework;
- preserve session continuity when a supported session or conversation identifier is supplied;
- reject unknown resident IDs clearly;
- include Estate metadata in a non-breaking extension field where practical;
- report fallback mode truthfully;
- never execute privileged actions;
- bind locally by default;
- no cloud dependency.

Streaming is optional. If unsupported, document and reject or ignore it truthfully.

### 5. Local Gateway Service and CLI

Preferred command shape:

```text
python -m estate.cli.main resident-gateway start --host 127.0.0.1 --port 11435
python -m estate.cli.main resident-gateway status --json
```

Use existing local server patterns where possible. Provide clear startup, occupied-port, status, and shutdown behavior. Gateway availability and local-model availability must be reported separately.

### 6. Open WebUI Setup Guide

Create:

`docs/residents/Open_WebUI_Estate_Resident_Gateway_Setup_v0_1.md`

Include:

- prerequisites;
- gateway startup;
- base URL;
- API-key placeholder behavior if Open WebUI requires one;
- model discovery;
- selecting Alfred and Helen;
- smoke-test prompts;
- troubleshooting for connection refusal, no models, provider unavailable, fallback mode, and stale browser state;
- statement that Open WebUI is only the conversation surface and the Estate remains authoritative.

### 7. Helen Activation Record

Create:

- `operations/residents/helen/WP-4001_helen_activation_report.md`
- `runtime/residents/helen/WP-4001_helen_activation_report.json`

Distinguish:

- code path implemented;
- Helen prompt loaded;
- model assignment or fallback;
- provider actually contacted or not;
- deterministic tests;
- manual Open WebUI validation pending or complete;
- Helen chat status;
- impact on Grace hiring readiness;
- known limitations.

Do not claim manual validation unless it happened.

## Tests

Cover at minimum:

- Alfred prompt remains Alfred-specific;
- Helen prompt is Helen-specific;
- mocked local-LLM Helen does not identify as Alfred or a generic assistant;
- per-resident model assignment and fallback;
- per-resident diagnostic paths;
- `/v1/models` includes Alfred and Helen;
- Grace is not exposed as active;
- `/v1/chat/completions` maps `estate/helen` correctly;
- OpenAI response envelope;
- unsupported model rejection;
- non-streaming behavior;
- deterministic fallback;
- no privileged execution;
- session persistence;
- bounded attachment behavior where supported;
- existing Alfred, Helen, and Office chat regressions.

Tests must not require cloud access, a real Open WebUI instance, a real GPU, or protected private characters. Mock the local provider where appropriate.

## Validation

Run focused tests for every changed module plus:

```powershell
CLS
Set-Location A:\theestate
python -m pytest `
  tests\test_resident_interaction.py `
  tests\test_steward_command_center.py `
  tests\test_helen_workforce.py `
  tests\test_helen_workforce_cli.py `
  tests\character_architecture\test_helen_resident_package.py `
  -q
```

Run the full suite if practical. Record unrelated failures honestly.

## Manual Acceptance

Start the gateway:

```powershell
CLS
Set-Location A:\theestate
python -m estate.cli.main resident-gateway start --host 127.0.0.1 --port 11435
```

Confirm models:

```powershell
CLS
Invoke-RestMethod http://127.0.0.1:11435/v1/models | ConvertTo-Json -Depth 10
```

Expected IDs:

```text
estate/alfred
estate/helen
```

Helen smoke test:

```powershell
CLS
$Body = @{
    model = 'estate/helen'
    messages = @(
        @{ role = 'user'; content = 'Who are you, what office do you serve, and what are your responsibilities?' }
    )
    stream = $false
} | ConvertTo-Json -Depth 10

Invoke-RestMethod `
    -Uri http://127.0.0.1:11435/v1/chat/completions `
    -Method Post `
    -ContentType 'application/json' `
    -Body $Body | ConvertTo-Json -Depth 20
```

The response must identify Helen and HR/Workforce Development and report provider/model/fallback state truthfully.

## Out of Scope

Do not activate Grace, create a second memory or authority system, replace Open WebUI, replace the Office UI, expose unrestricted journals, add cloud dependencies, redesign Helen, alter constitutional governance, or inspect protected private characters.

## Required Completion Evidence

Write:

- `operations/validation/reports/WP-4001_multi_resident_chat_gateway_and_helen_activation.md`
- `collaboration/work_packages/completions/WP-4001_codex_done.json`

The receipt must record files changed, tests run, provider calls made or skipped, Open WebUI manual validation status, Helen chat activation status, Grace status, and known limitations.

Required receipt fields:

- `work_package_id`
- `status`
- `summary`
- `files_changed`
- `validation_commands`
- `validation_results`
- `manual_open_webui_validation_status`
- `helen_identity_prompt_status`
- `helen_local_llm_path_status`
- `resident_gateway_status`
- `available_resident_models`
- `local_provider_called`
- `cloud_provider_called`
- `privileged_action_executed_from_chat`
- `grace_appointed_or_activated`
- `known_limitations`
- `completed_at`

Expected values:

```text
cloud_provider_called = false
privileged_action_executed_from_chat = false
grace_appointed_or_activated = false
```

## Completion Standard

WP-4001 is complete only when Alfred and Helen use resident-specific prompts through one shared framework, Helen has a real local-LLM path, `/v1/models` and `/v1/chat/completions` work locally, Open WebUI setup documentation exists, existing Alfred and Helen functionality remains green, and Grace remains unappointed and inactive.
