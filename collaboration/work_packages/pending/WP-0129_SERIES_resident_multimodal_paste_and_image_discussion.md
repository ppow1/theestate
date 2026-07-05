# SERIES TASK WP-0129 — Resident Multimodal Paste and Image Discussion

## Codex Command

Read collaboration/work_packages/pending/WP-0129_SERIES_resident_multimodal_paste_and_image_discussion.md and do exactly what it says.

## Mode

SERIES

## Mission

Add local-first multimodal paste support to the resident interaction framework and Alfred Operations Center chat so the Steward can paste screenshots, images, and text snippets into a resident conversation and ask Alfred to inspect, summarize, or discuss them.

## Problem Statement

The Steward frequently works by copying and pasting terminal output, webpage fragments, UI screenshots, ComfyUI screenshots, GitHub screens, and local application screen grabs. Alfred currently accepts typed text only. He cannot receive a screenshot pasted into chat, store it as a resident conversation artifact, or discuss what it contains.

This blocks a major resident-assistance workflow.

## Required Design Position

Pasted images and text snippets are resident conversation artifacts. They must be local, persisted, linked to conversation turns, governed by memory/redaction rules, and never sent to cloud vision APIs.

If a local vision-capable model is available, use it. If no local vision model is available, store the image and respond truthfully that visual inspection is not yet available.

## Preconditions

1. Confirm WP-0126, WP-0127, and WP-0128 are merged.
2. Inspect `src/estate/core/resident_interaction.py` for the current turn schema and LLM adapter path.
3. Inspect `src/estate/core/steward_command_center.py` for the Alfred chat form, JavaScript, and resident API handlers.
4. Inspect existing forget/redaction behavior and runtime artifact conventions.
5. Inspect local model/provider discovery to determine whether any available local model supports image input.

If a precondition fails, stop and report the blocker.

## Scope

In scope:

1. Add resident conversation attachment support for pasted images and pasted text snippets.
2. Add browser paste handling to Alfred chat.
3. Add local API support for receiving chat messages with attachments.
4. Persist pasted images under bounded local resident interaction storage.
5. Link attachment metadata to resident conversation turns.
6. Display attachment metadata and a safe local thumbnail or link in Alfred history.
7. Add a local-only vision/multimodal adapter boundary.
8. Use a local vision-capable model when available.
9. Return truthful `vision_unavailable` fallback when no local vision model is available.
10. Extend forget/redaction behavior to suppress attachment contents from normal history.
11. Add tests and WP-0129 validation/receipt artifacts.

Out of scope:

- Cloud vision APIs.
- Remote upload.
- Public file serving beyond local server boundaries.
- Full OCR pipeline unless a local utility already exists and is safe to reuse.
- General document ingestion.
- Image generation.
- Action execution from image interpretation.
- Rebuilding the Operations Center UI.

## Required User Experience

The Steward must be able to:

1. Open Alfred chat.
2. Paste a screenshot/image from the clipboard.
3. See a pending attachment before sending.
4. Add text such as `Alfred, what do you notice in this screenshot?`.
5. Send the turn.
6. Receive a truthful answer:
   - if vision is available, Alfred discusses the image;
   - if vision is unavailable, Alfred says the image was received and stored but cannot yet be visually inspected.
7. Reload history and see the attachment metadata linked to the turn.

## Required Attachment Model

Implement or document and validate an attachment structure equivalent to:

```json
{
  "attachment_id": "attach_0001",
  "kind": "image|text_snippet",
  "source": "clipboard_paste|file_upload|api",
  "created_at": "ISO-8601 timestamp",
  "original_filename": "clipboard-image.png",
  "mime_type": "image/png",
  "size_bytes": 123456,
  "storage_path": "runtime/resident_interactions/attachments/alfred/.../clipboard-image.png",
  "sha256": "...",
  "redaction_status": "active|forgotten|redacted",
  "vision_status": "not_attempted|processed|unavailable|failed",
  "vision_provider": "ollama|local_adapter|none",
  "vision_model": "model name if known",
  "summary": "optional local summary if available"
}
```

Resident turns must include an `attachments` list with safe metadata references.

## Required API / Server Changes

Extend local resident chat to support attachments using either multipart/form-data or JSON/base64 payloads. The report must document the chosen design.

Acceptable endpoint designs:

```text
POST /api/residents/{resident_id}/chat
```

or:

```text
POST /api/residents/{resident_id}/attachments
POST /api/residents/{resident_id}/chat
```

All storage must be bounded to resident interaction runtime paths and must not expose arbitrary filesystem access.

## Required UI Changes

Update Alfred chat to support:

- clipboard image paste;
- clipboard text snippet paste where useful;
- pending attachment display;
- remove pending attachment before send;
- send text and attachments together;
- mode/source display remains visible;
- history display of attachment metadata and safe thumbnail/link;
- graceful message if browser paste APIs are unavailable.

## Required Safety Boundaries

1. Attachments remain local Estate artifacts.
2. No cloud vision calls.
3. No action execution based on image interpretation.
4. Resident responses must distinguish observation from action.
5. Forget/redaction covers both text and attachments.
6. Attachment links must not expose arbitrary local files.

## Required Artifacts

Create:

`operations/residents/alfred/WP-0129_resident_multimodal_paste_report.md`

Create machine-readable companion:

`runtime/residents/alfred/WP-0129_resident_multimodal_paste_report.json`

The report must include attachment storage path, schema summary, API design, UI paste behavior, local vision adapter status, detected vision-capable models if any, fallback behavior, example pasted-image turn metadata, forget/redaction behavior, tests run, validation commands run, known limitations, and recommended next action.

## Required Tests

Add or update tests for:

1. Attachment metadata creation.
2. Image persistence under bounded resident attachment storage.
3. Attachment id linked to a conversation turn.
4. Chat endpoint accepts text plus attachment payload.
5. Unsafe paths or unsupported payloads are rejected.
6. History reload includes attachment metadata but not unsafe paths.
7. Forget/redaction suppresses attachment content.
8. Vision adapter reports unavailable truthfully when no vision model exists.
9. Mocked vision adapter can produce an image summary.
10. Alfred uses mocked image summary when vision is available.
11. Alfred does not fake image inspection when vision is unavailable.
12. UI HTML/JavaScript includes paste handling and pending attachment display.
13. Existing WP-0126/WP-0127/WP-0128 tests remain passing.

Run:

```bash
PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q
PYTHONPATH=src python -m pytest tests/test_resident_conversation_sessions.py tests/test_resident_authority.py tests/test_resident_interaction.py tests/test_steward_command_center.py -q
```

## Required Validation Commands

Run or document equivalent:

```bash
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0126 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0127 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0128 --json
PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0129 --json
PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json
```

Also document a Steward-local smoke test: open Office of the Steward, paste screenshot into Alfred chat, send a question about the image, verify attachment persistence and truthful response.

## Required Outputs

- Resident attachment model/storage.
- Chat attachment API path.
- Alfred paste UI.
- Attachment history display.
- Local vision adapter boundary.
- Vision unavailable fallback.
- Attachment forget/redaction behavior.
- WP-0129 report Markdown and JSON.
- WP-0129 validation recipe and runtime validation artifacts.
- `collaboration/work_packages/completions/WP-0129_codex_done.json`.

## Completion Artifact

Create:

`collaboration/work_packages/completions/WP-0129_codex_done.json`

It must include `work_package_id = WP-0129`, `codex_status = done`, summary, attachment storage path, API design, UI changes, local vision status, fallback behavior, tests run, validation commands run, known limitations, recommended next action, `ready_for_ca_review = true`, and `merge_authority = ca_verified_auto_merge_allowed`.

## Acceptance Criteria

WP-0129 is complete when the Steward can paste an image/screenshot into Alfred chat, the image is stored locally as a resident conversation artifact, the turn records attachment metadata, history reload displays the attachment reference safely, Alfred uses a local vision model if available, and Alfred truthfully reports inability to inspect images if no local vision model is available.

## Merge Class

Class A. Escalate only if implementation requires changing server exposure/security policy, memory/redaction policy, resident API governance, cloud model dependency policy, or production-readiness semantics.
