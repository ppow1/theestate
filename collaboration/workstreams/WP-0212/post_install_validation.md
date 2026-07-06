# WP-0212 Post-install Validation

- PASS: `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0200 --json`
- PASS: `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0201 --json`
- PASS: `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0202 --json`
- PASS: `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0204 --json`
- PASS: `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0205 --json`
- PASS: `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0206 --json`
- PASS: `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0208 --json`
- PASS: `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0209 --json`
- PASS: `PYTHONPATH=src python -m estate.cli.main workstream validate --id WP-0210 --json`
- PASS: `PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json`
- PASS: `PYTHONPATH=src pytest tests/test_office_actions.py tests/test_office_settings_help_about_actions.py tests/test_office_work_package_actions.py tests/test_office_validation_actions.py tests/test_office_planning_actions.py tests/test_office_communications_actions.py tests/test_office_board_actions.py tests/test_office_resident_actions.py tests/test_office_ai_service_actions.py tests/test_steward_command_center.py -q`
- PASS: `PYTHONPATH=src python -m estate.cli.main steward-command-center --json`

Note: production-readiness command returned exit 0 while reporting existing repository-wide blockers unrelated to WP-0212.

- WARNING: `PYTHONPATH=src python -m estate.cli.main validate-work-package --id WP-0212 --json` exited 1 because no validation recipe is registered and the validator still reports a receipt key gap despite the WP-0212 receipt containing `pull_request_url_or_not_applicable_reason`; the command generated review artifacts for CA inspection.
