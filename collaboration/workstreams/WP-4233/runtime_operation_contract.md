# Runtime operation contract

All operations return `estate.grace-runtime-bridge.v1` envelopes. Successful payloads retain the exact runtime response under `payload`/`raw` and identify `source_system`, `source_operation`, and retrieval context. The runtime itself remains authoritative for lifecycle, persistence, replay, readiness, audit, and provider state.

Registered reads: `get_current_objective`, `get_objective_by_id`, `get_runtime_readiness`, `get_runtime_availability`, `get_lifecycle_projection`, `get_replay_cursor`, `get_recent_lifecycle_events`, `get_provider_admission`, `get_last_dispatch`, `get_last_provider_result`, `get_last_reconciliation`, `get_last_validation`, `get_last_grace_receipt`, `get_current_blocker`, `get_responsible_office`, `get_next_lawful_action`, and `list_grace_runtime_operations`.

No `POST /v1/commands` operation is present in the Tool source.
