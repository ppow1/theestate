# WP-0130 Gateway Vision Validation-and-Repair Follow-on

## Verdict

The implementation repair is complete and deterministic acceptance passes. Live vision acceptance is blocked in this environment because the configured Ollama endpoint did not answer `GET /api/tags`; consequently `/api/show` could not be inspected and no compatible installed model could be selected. No model was installed or pulled.

## Exact root cause

The failure was at the Resident Gateway transport boundary. Open WebUI sent an OpenAI-compatible multimodal user message. `resident_gateway._message_text` retained only text parts and discarded `image_url`/file parts, while `_chat_result` invoked `process_chat` without its `attachments` argument. Ingrid therefore received only the text plus Open WebUI's filename-level context. `LocalVisionAdapter`, attachment byte persistence, visual-summary prompt injection, and resident interpretation were never entered. WP-0130 itself was not resident-gated inside `process_chat`; its configuration was already loaded by the shared adapter, despite living under the legacy Alfred path.

## Repair

The canonical gateway now normalizes image data URLs, direct base64 upload metadata, Open WebUI `file` wrappers, message/payload `attachments` and `files`, and bounded pre-stored attachment paths. It passes normalized attachments to the existing `process_chat` boundary for all eight exposed residents and for Conference Room turns. `create_attachment` reads pre-stored bytes only from `runtime/resident_interactions/attachments`, copies them into the requesting turn's bounded store, invokes the existing `LocalVisionAdapter`, and bounds summaries to 1,200 characters. Raw image bytes/data URLs never enter resident prompts, persisted session JSON, diagnostics, logs, or this report.

The vision model remains an observation-only provider. Its bounded summary is supplied as context to the selected resident's existing Campaign 08 prompt; it is not presented as the resident and cannot authorize execution.

## Configuration and local discovery

- Canonical configuration (shared by all residents): `runtime/residents/alfred/vision_model_config.json`
- Provider: local Ollama at `http://127.0.0.1:11434`
- Preferred candidate: `llama3.2-vision:11b`
- Cloud allowed: `false`
- `GET /api/tags`: connection refused on 2026-07-20
- `POST /api/show`: not possible because no tag/model was detected
- Detected models: none (Ollama unavailable from this environment)
- Selected model: none
- Automatic installation/pull: not performed

Exact Steward-approved install command if the host has no compatible model:

```bash
ollama pull llama3.2-vision:11b
```

## Manual Open WebUI acceptance

1. On the Resident Gateway host, run `curl http://127.0.0.1:11434/api/tags` and confirm `llama3.2-vision:11b`; if absent, obtain Steward approval before running the command above.
2. Restart Resident Gateway so it uses this revision.
3. Start a new direct Ingrid chat in Open WebUI.
4. Attach a known PNG, JPEG, WebP, or GIF image.
5. Ask: **Can you tell me what this is?**
6. Confirm Ingrid describes visible content rather than only a filename/MIME type, while retaining Ingrid's privacy-oriented voice.
7. Inspect `runtime/resident_interactions/sessions/<chat-id>.json` and confirm the attachment records `vision_status: processed`, `vision_provider: ollama`, `vision_model: llama3.2-vision:11b`, and a bounded `summary`.
8. Repeat once through Conference Room where attachments are supported to confirm the same boundary.
9. If Ollama is unavailable, confirm the image remains stored, metadata says `vision_status: unavailable`, and Ingrid explicitly says she could not visually inspect it.

## Focused validation

The focused suite covers all eight gateway residents, Ingrid's regression, OpenAI image content, uploaded-file metadata, bounded stored paths, persisted metadata, absence of raw bytes in session records, truthful fallback, canonical shared configuration, and direct/Conference Room parity. Existing resident interaction and gateway suites also pass. Full work-package and production-readiness validation results are recorded in the completion receipt.
