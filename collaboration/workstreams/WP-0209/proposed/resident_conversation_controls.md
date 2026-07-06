# WP-0209 — Resident Conversation Controls

## Alignment
WP-0200 staged vocabulary was available and used for action classes, authority classes, confirmation requirements, fail-closed behavior, and local-only guarantees.

## Staged Controls

### Alfred
- `alfred.start_alfred_conversation` — see `action_metadata.json`; local-only; staged, not installed.
- `alfred.inspect_alfred_surface` — see `action_metadata.json`; local-only; staged, not installed.
- `alfred.copy_alfred_duty_status_commands` — see `action_metadata.json`; local-only; staged, not installed.
- `alfred.queue_alfred_request` — see `action_metadata.json`; local-only; staged, not installed.
- `alfred.inspect_alfred_job_request` — see `action_metadata.json`; local-only; staged, not installed.
- `alfred.cancel_retry_job_design` — see `action_metadata.json`; local-only; staged, not installed.

### Helen
- `helen.inspect_helen_surface` — see `action_metadata.json`; local-only; staged, not installed.
- `helen.copy_helen_duty_status_authority_commands` — see `action_metadata.json`; local-only; staged, not installed.
- `helen.start_helen_conversation` — see `action_metadata.json`; local-only; staged, not installed.
- `helen.draft_hr_onboarding_request` — see `action_metadata.json`; local-only; staged, not installed.

### Resident Conversations
- `resident_conversations.start_session` — see `action_metadata.json`; local-only; staged, not installed.
- `resident_conversations.open_transcript` — see `action_metadata.json`; local-only; staged, not installed.
- `resident_conversations.export_transcript` — see `action_metadata.json`; local-only; staged, not installed.
- `resident_conversations.redact_forget_with_audit_design` — see `action_metadata.json`; local-only; staged, not installed.
- `resident_conversations.draft_promotion_of_outcome` — see `action_metadata.json`; local-only; staged, not installed.
- `resident_conversations.inspect_authority_boundary` — see `action_metadata.json`; local-only; staged, not installed.

## Safety Notes
- Staged work is not installed into active Office runtime files.
- Review requests are not approvals; promotion creates drafts/proposals only.
- No deletion, cloud calls, telemetry, resident authority expansion, service startup, or model load is introduced.
- Exports include sensitivity warnings and remain local-only.
