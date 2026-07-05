# WP-0129 Resident Multimodal Paste Report

## Summary
WP-0129 adds local-first resident conversation attachments for pasted images and text snippets. Alfred chat now accepts clipboard images and long text snippets, previews pending attachments before send, persists them as bounded local artifacts, links safe metadata to resident turns, displays attachment history with safe local thumbnails, and uses a local-only vision adapter boundary when a local vision-capable Ollama model is detected.

## Attachment storage path
Attachments are stored under `runtime/resident_interactions/attachments/{resident_id}/{session_id}/`. The server only serves thumbnails from `runtime/resident_interactions/attachments/` and rejects arbitrary file paths.

## Schema summary
Each turn can include an `attachments` list with `attachment_id`, `kind`, `source`, `created_at`, `original_filename`, `mime_type`, `size_bytes`, `storage_path`, `sha256`, `redaction_status`, `vision_status`, `vision_provider`, `vision_model`, and optional `summary`.

## API design
Chosen design: `POST /api/residents/{resident_id}/chat` with JSON payloads. The payload can include `message`, `action`, `session_id`, and `attachments[]`. Image attachments use base64 as `data_base64`; text snippets use `text`. Unsupported MIME types and malformed attachment objects are rejected by the resident interaction layer.

## UI paste behavior
The Alfred Operations Center chat textarea listens for paste events. Clipboard images are converted to base64 pending attachments, long clipboard text is captured as a `text_snippet`, pending attachments are displayed with remove buttons, and the send action posts text plus attachments together. History reload displays metadata and a safe thumbnail URL for image attachments.

## Local vision adapter status
`LocalVisionAdapter` is a local-only Ollama boundary that discovers likely vision-capable models by local model names and calls Ollama `/api/generate` with image data only when such a local model is available. No cloud vision APIs are used.

## Detected vision-capable models
Current local discovery result: no local vision-capable model discovered.

## Fallback behavior
When no local vision-capable model is available, Alfred stores the image and truthfully appends that the pasted image was received and stored locally but cannot yet be visually inspected. Alfred does not fake image inspection.

## Example pasted-image turn metadata
```json
{
  "attachment_id": "attach_0001",
  "kind": "image",
  "source": "clipboard_paste",
  "mime_type": "image/png",
  "storage_path": "runtime/resident_interactions/attachments/alfred/<session>/attach_0001_clipboard-image.png",
  "redaction_status": "active",
  "vision_status": "unavailable",
  "vision_provider": "none",
  "vision_model": null
}
```

## Forget/redaction behavior
Steward-directed `forget_conversation()` redacts turn text and resident response, suppresses forgotten turns from normal history, marks attachment metadata `redaction_status` as `forgotten` or requested status, and removes attachment summaries from forgotten turn records.

## Tests run
- `PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q`
- `PYTHONPATH=src python -m pytest tests/test_resident_conversation_sessions.py tests/test_resident_authority.py tests/test_resident_interaction.py tests/test_steward_command_center.py -q`
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0126 --json`
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0127 --json`
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0128 --json`
- `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0129 --json`
- `PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json`

## Validation command notes
The pytest suites passed. WP-0126/WP-0127/WP-0128 validation commands were run and currently fail due pre-existing chained validation dependency on missing/failed WP-0123 validation, not due WP-0129 attachment code. WP-0129 validation was registered as part of this work package.

## Steward-local smoke test
Open the Office of the Steward, paste a screenshot into Alfred chat, verify the pending attachment appears, enter a question, send, and confirm the response states either a local image observation from a local vision model or the truthful vision-unavailable fallback. Reload history and verify the attachment metadata and safe thumbnail remain linked to the turn.

## Known limitations
- Vision-capable model detection uses local Ollama model-name hints.
- No OCR pipeline was added.
- Browser paste behavior depends on browser clipboard APIs.
- Image content is persisted locally until Steward-directed retention cleanup or redaction policies remove/suppress it.

## Recommended next action
Install or configure a local vision-capable Ollama model such as a LLaVA-family model and run the Steward-local smoke test against a real screenshot.
