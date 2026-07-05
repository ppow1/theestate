# SERIES TASK WP-0130 — Local Vision Model Enablement for Resident Image Discussion

## Codex Command

Read collaboration/work_packages/pending/WP-0130_SERIES_local_vision_model_enablement_for_resident_images.md and do exactly what it says.

## Mode

SERIES

## Mission

Enable Alfred and the resident interaction framework to actually inspect pasted screenshots/images using a local vision-capable model when one is installed.

WP-0129 successfully added image paste, bounded local attachment storage, and truthful fallback. Alfred can now receive and store screenshots, but he reports that no local vision-capable model is available. WP-0130 closes that gap by defining, detecting, and using a local vision model path.

## Problem Statement

The Steward can paste screenshots into Alfred chat, and the Estate stores those screenshots locally under resident interaction attachment storage. However, Alfred cannot visually inspect them yet because the local model set currently exposed to the Estate is text-oriented.

This is the next required capability for real operational assistance, because the Steward frequently works by pasting screenshots of terminals, GitHub pages, UI states, ComfyUI workflows, and local application errors.

## Preconditions

1. Confirm WP-0126, WP-0127, WP-0128, and WP-0129 are merged.
2. Confirm image attachments are stored under `runtime/resident_interactions/attachments`.
3. Inspect `LocalVisionAdapter` or equivalent vision boundary added by WP-0129.
4. Inspect current Ollama model discovery behavior.
5. Confirm no cloud vision API is used.

If any precondition fails, stop and report the exact blocker.

## Scope

In scope:

1. Define a local vision model configuration path for resident image inspection.
2. Detect local Ollama models that support image input.
3. Prefer an explicitly configured resident vision model when present.
4. Provide a clear install/configuration report if no vision model exists.
5. Wire Alfred pasted-image turns to local vision inspection when a compatible model is available.
6. Persist vision provider/model/status/summary metadata on attachments.
7. Ensure Alfred answers image questions using the local vision summary when available.
8. Keep truthful fallback when no vision-capable local model exists.
9. Add tests using a mocked local vision model.
10. Add WP-0130 validation recipe and completion receipt.

Out of scope:

- Cloud vision APIs.
- Image generation.
- OCR-only pipeline unless used as an optional local fallback.
- General file manager.
- Action execution based on image interpretation.
- Installing a model automatically without Steward approval.
- Launching/managing services such as ComfyUI or SillyTavern. That belongs in a separate Estate Service Manager work package.

## Local Vision Model Guidance

The implementation should support local Ollama vision-capable models where possible. Do not assume a text-only model can see images.

Candidate model names may include local vision models such as:

- `llava`
- `llava:latest`
- `llava:7b`
- `llama3.2-vision`
- `llama3.2-vision:11b`
- other model names whose Ollama metadata or configuration indicates image capability

The Estate should not hardcode only one model if a configurable model path is straightforward.

## Required Configuration

Create or update a local-first configuration artifact such as:

`runtime/residents/alfred/vision_model_config.json`

or a more canonical existing path if found.

The config should be able to represent:

```json
{
  "provider": "ollama",
  "endpoint": "http://127.0.0.1:11434",
  "preferred_model": "llama3.2-vision:11b",
  "fallback_behavior": "vision_unavailable",
  "cloud_allowed": false
}
```

If no compatible local vision model is installed, the report must include explicit Steward install guidance but must not install without approval.

## Required Behavior

When Alfred receives a turn with an image attachment and a compatible local vision model exists:

1. Alfred sends the image to the local vision adapter.
2. The adapter returns a concise visual summary.
3. The attachment metadata records `vision_status = processed`.
4. The attachment metadata records provider/model.
5. Alfred uses that visual summary in his answer.
6. Alfred still observes authority boundaries and does not execute actions from image content.

When no compatible model exists:

1. The image remains stored.
2. The attachment metadata records `vision_status = unavailable`.
3. Alfred truthfully says visual inspection is unavailable.
4. Alfred may discuss any pasted text or metadata.

## Required Artifacts

Create:

`operations/residents/alfred/WP-0130_local_vision_model_enablement_report.md`

Create machine-readable companion:

`runtime/residents/alfred/WP-0130_local_vision_model_enablement_report.json`

The report must include:

- current git commit;
- detected Ollama models;
- detected vision-capable models;
- selected vision model, if any;
- configuration path;
- adapter behavior;
- example image prompt with mocked or real vision result;
- fallback behavior;
- tests run;
- validation commands run;
- known limitations;
- recommended Steward install command if no local vision model is available.

## Required Tests

Add or update tests for:

1. Vision-capable model detection.
2. Configured vision model preference.
3. No-cloud guarantee.
4. Mocked local vision model summary.
5. Attachment metadata records processed vision status when mock vision succeeds.
6. Attachment metadata records unavailable when no vision model exists.
7. Alfred uses vision summary in image-question response.
8. Alfred does not fake visual inspection when unavailable.
9. Existing WP-0129 attachment tests remain passing.

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m pytest tests/test_resident_interaction.py tests/test_steward_command_center.py -q
```

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0129 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0130 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Also document a Steward-local smoke test:

```text
Install or confirm a local Ollama vision model -> restart Operations Center -> paste screenshot into Alfred chat -> ask what Alfred sees -> verify mode remains local and attachment vision_status is processed.
```

## Required Outputs

- Local vision model configuration artifact.
- Vision-capable model detection.
- Local vision adapter integration for pasted image attachments.
- Attachment vision metadata updates.
- Alfred response integration using vision summaries.
- WP-0130 report Markdown and JSON.
- WP-0130 validation recipe and runtime validation artifacts.
- `collaboration/work_packages/completions/WP-0130_codex_done.json`.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0130_codex_done.json`

It must include `work_package_id = WP-0130`, `codex_status = done`, summary, vision config path, detected models, selected model if any, fallback behavior, tests run, validation commands run, known limitations, recommended next action, `ready_for_ca_review = true`, and `merge_authority = ca_verified_auto_merge_allowed`.

## Acceptance Criteria

WP-0130 is complete when the Estate can detect and configure local vision-capable models, Alfred can use a local vision summary for pasted screenshots when available, fallback remains truthful when not available, and all image handling remains local and governed.

## Merge Class

Class A. Escalate only if implementation requires changing cloud model policy, server exposure/security policy, resident API governance, memory/redaction policy, or production-readiness semantics.
