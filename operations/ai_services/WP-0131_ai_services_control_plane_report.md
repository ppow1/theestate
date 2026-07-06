# AI Services Discovery Report

Generated: 2026-07-06T00:05:47.513840+00:00

## Services
- comfyui — ComfyUI (http://127.0.0.1:8188)
- ollama — Ollama (http://127.0.0.1:11434)
- open_webui — Open WebUI (http://127.0.0.1:8080)
- sillytavern — SillyTavern (http://127.0.0.1:8000)
- textgen — Text Generation WebUI (http://127.0.0.1:5000/v1)

## WP-0131 Control Plane Report

- **work_package_id**: WP-0131
- **git_commit**: 02da2068a34cf67d55f500103b2aee76eb76e7b5
- **subsystem_paths**: ['src/estate/ai_services', 'runtime/ai_services', 'operations/ai_services']
- **manifest_schema_summary**: ['service_id', 'display_name', 'service_type', 'local_only', 'host_policy', 'default_endpoint', 'ports', 'paths', 'operations', 'approval']
- **seeded_service_manifests**: ['comfyui', 'ollama', 'open_webui', 'sillytavern', 'textgen']
- **rediscovery_behavior**: Scans runtime/ai_services/implementations/*/service.manifest.json, validates safety/schema, rejects unsafe manifests, rebuilds registry, preserves state.
- **registry_path**: runtime/ai_services/registry.json
- **state_path**: runtime/ai_services/state.json
- **audit_log_path**: runtime/ai_services/audit_log.jsonl
- **cli_commands_added**: ['ai-services status', 'ai-services rediscover', 'ai-services start', 'ai-services stop', 'ai-services load-model']
- **api_endpoints_added**: ['GET /ai-services/status', 'GET /ai-services/services', 'GET /ai-services/services/{service_id}', 'POST /ai-services/services/{service_id}/start', 'POST /ai-services/services/{service_id}/stop', 'POST /ai-services/services/{service_id}/models/load', 'POST /ai-services/rediscover']
- **policy_gates**: ['loopback_only', 'cloud_rejected_by_default', 'steward_approval_for_model_load', 'unknown_operations_rejected', 'stop_requires_manifest_and_approval', 'public_bind_rejected', 'alfred_bounded_operations']
- **alfred_facing_contract**: Alfred may request only modeled operations through CLI/API with Steward approval where required; no unrestricted host command access is granted.
- **model_location_handling**: Model directories are recorded per manifest as facts; no files are moved or consolidated.
- **tests_run**: ['PYTHONPATH=src pytest tests/test_ai_services_control_plane.py -q', 'PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q']
- **validation_commands_run**: ['PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0131 --json', 'PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json']
- **known_limitations**: ['Operations are planned/audited only; no third-party service process is launched by this work package.', 'Local Windows paths are recorded as manifest facts from the work package.']
- **recommended_next_action**: CA review, then a future package may add Steward UI approval workflow and process execution adapters.
- **ready_for_ca_review**: True
