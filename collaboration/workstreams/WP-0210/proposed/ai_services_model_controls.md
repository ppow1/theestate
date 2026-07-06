# WP-0210 — AI Services / Model Controls

## Alignment
WP-0200 staged vocabulary was available and used for action classes, authority classes, confirmation requirements, fail-closed behavior, and local-only guarantees.

## Staged Controls

### Ai Services Models
- `ai_services_models.inspect_service_model_manifest` — see `action_metadata.json`; local-only; staged, not installed.
- `ai_services_models.refresh_rediscovery_design` — see `action_metadata.json`; local-only; staged, not installed.
- `ai_services_models.sync_local_model_provider_inventory_design` — see `action_metadata.json`; local-only; staged, not installed.
- `ai_services_models.copy_start_stop_load_commands` — see `action_metadata.json`; local-only; staged, not installed.
- `ai_services_models.request_service_model_approval` — see `action_metadata.json`; local-only; staged, not installed.
- `ai_services_models.inspect_approval_audit_history` — see `action_metadata.json`; local-only; staged, not installed.
- `ai_services_models.inspect_resident_model_assignment_state` — see `action_metadata.json`; local-only; staged, not installed.
- `ai_services_models.export_ai_services_snapshot` — see `action_metadata.json`; local-only; staged, not installed.

## Safety Notes
- Staged work is not installed into active Office runtime files.
- Review requests are not approvals; promotion creates drafts/proposals only.
- No deletion, cloud calls, telemetry, resident authority expansion, service startup, or model load is introduced.
- Exports include sensitivity warnings and remain local-only.
