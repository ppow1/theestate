# WP-4029 Integration Notes

WP-4029 is staged and uninstalled. WP-4031 should adapt the contract in
`src/resident_attachment_exchange.py` into the existing Estate resident
attachment storage, mailbox/conversation bus, delegated task records, resident
session manager, classification, audit, Office, Open WebUI, and CLI surfaces.

## Installation guidance for WP-4031

- Preserve source links for message, task, session, conversation, source kind,
  and source id on every attachment record.
- Use existing storage primitives, but keep deterministic paths equivalent to
  `resident_attachments/{owner}/{resident}/{source_kind}/{source_id}/{checksum-prefix}/{attachment_id}.{ext}`.
- Keep summaries as separate working artifacts that reference original checksums;
  never treat summary text as source content.
- Keep dangerous extension, size, media-type, and unsupported extension failures
  closed and audited where the production audit runtime supports rejection events.
- Route sensitive reads, downloads, exports, retention changes, and redactions to
  the existing audit mechanism.
- Expose Office/Open WebUI cards using metadata and download handles only; do not
  expose protected attachments publicly or execute uploaded content.
- Add CLI wiring in `src/estate/cli/main.py` only during WP-4031 installation.

## Boundaries

This stage does not install active integrations, create a cloud drive, execute
uploaded files, call live model adapters, or write outside `collaboration/workstreams/WP-4029/`.
