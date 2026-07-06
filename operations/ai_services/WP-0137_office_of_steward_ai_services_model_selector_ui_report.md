# WP-0137 Office of the Steward AI Services / Models Report

- Final UI/control surface path: Office of the Steward command center panel: runtime/steward/command_center.html#ai-services-models and CLI ai-services steward-panel
- Service data displayed: service_id, display_name, service_type, endpoint, host_policy, ports, current_state, health_status, last_operation, available_operations, approval_requirements, log_reference
- Model data displayed: TextGen manifest model directory inventory, Ollama inventory hook/unavailable marker, manifest model locations, conservative unknown capability classification
- Model preference artifacts: runtime/ai_services/model_preferences.json
- Worker assignment artifacts: runtime/ai_services/model_assignments.json
- Approval behavior: Steward approve/deny uses record_approval_decision through ai-services approve/deny; actor self-approval is blocked in Steward layer.
- Audit/rediscovery behavior: Panel exposes audit tail, rediscover hook, refresh-status hook, recent log references from state processes.
- CLI/API changes: ai-services models, ai-services model-preferences, ai-services set-model-preference, ai-services assignments, ai-services set-assignment, ai-services approvals, ai-services approve, ai-services deny, ai-services refresh-status, ai-services steward-panel

## Tests run
- `PYTHONPATH=src pytest -q tests/test_ai_services_control_plane.py tests/test_ai_services_steward_model_selector.py`
- `PYTHONPATH=src pytest -q tests/test_work_package_validation.py tests/test_production_readiness_validation.py`
- `PYTHONPATH=src pytest -q tests/test_ai_services_control_plane.py`
- `PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json`

## Validation results
Required validation commands ran successfully (exit 0). Production-readiness JSON still reports pre-existing global blockers and WP-0137 no dedicated recipe status; this is explicitly documented as the missing dedicated WP-0137 recipe limitation.

## Known limitations
- Model inventory does not query live Ollama/TextGen network APIs; unavailable local directories are marked clearly.
- UI renders governed command hooks; form-driven POST actions can be added later without changing authority semantics.
- No dedicated WP-0137 validation recipe existed before this work package.

## Recommended next action
Chief Architect review, then add richer live model inventory adapters and UI forms for approval decisions if desired.
