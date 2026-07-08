# WP-0218 Estate Model Control Plane Report

- **work_package_id**: WP-0218
- **generated_at**: 2026-07-08T18:17:07+00:00
- **root_cause**: Model selection lived inside adapters/resident defaults rather than an Estate-governed model-control layer.
- **paths**: ['src/estate/model_control', 'runtime/model_control', 'operations/model_control']
- **registry_schema_summary**: ['model_id', 'provider', 'service_id', 'model_name', 'endpoint', 'capabilities', 'capability_confidence', 'context_length', 'size_bytes', 'discovered_at', 'available', 'local_only', 'cloud_allowed']
- **assignment_schema_summary**: ['estate_defaults', 'residents', 'workers', 'authority']
- **authority_policy_summary**: Actor capability authority plus model capability validation; cloud disallowed by default; Steward approval required for assignment changes.
- **office_ui_changes**: AI Services / Models panel now includes Estate model-control registry, assignments, authority, diagnostics, and audit artifacts.
- **cli_commands_added**: ['model-control rediscover', 'model-control list-models', 'model-control assignments', 'model-control set-default', 'model-control assign', 'model-control validate-assignments']
- **alfred_integration_changes**: Alfred resolves text selection through model_control assignments/policy before adapter invocation and labels bootstrap fallback explicitly.
- **tests_run**: ['PYTHONPATH=src pytest tests/test_model_control.py -q', 'PYTHONPATH=src pytest tests/test_model_control.py tests/test_resident_interaction.py tests/test_steward_command_center.py -q', 'PYTHONPATH=src pytest tests/test_work_package_validation.py tests/test_production_readiness_validation.py -q']
- **validation_commands_run**: ['PYTHONPATH=src python -m estate.cli.main model-control rediscover --json', 'PYTHONPATH=src python -m estate.cli.main model-control validate-assignments --json', 'PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0218 --json', 'PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json']
- **known_limitations**: ['Runtime Ollama fetching is opt-in and mocked in tests; no models are installed or downloaded.']
- **recommended_next_action**: CA review and Steward selection of production preferred vision/code models when local models are available.
- **ready_for_ca_review**: True
