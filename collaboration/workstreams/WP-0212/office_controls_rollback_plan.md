# WP-0212 Rollback Plan

## Active files modified
- `src/estate/core/office_actions.py`
- `src/estate/core/office_settings_help_about_actions.py`
- `src/estate/core/office_work_package_actions.py`
- `src/estate/core/office_validation_actions.py`
- `src/estate/core/office_planning_actions.py`
- `src/estate/core/office_communications_actions.py`
- `src/estate/core/office_board_actions.py`
- `src/estate/core/office_resident_actions.py`
- `src/estate/core/office_ai_service_actions.py`
- `tests/test_office_actions.py`
- `tests/test_office_settings_help_about_actions.py`
- `tests/test_office_work_package_actions.py`
- `tests/test_office_validation_actions.py`
- `tests/test_office_planning_actions.py`
- `tests/test_office_communications_actions.py`
- `tests/test_office_board_actions.py`
- `tests/test_office_resident_actions.py`
- `tests/test_office_ai_service_actions.py`

## Source staged artifacts
- `collaboration/workstreams/WP-0200/proposed/`
- `collaboration/workstreams/WP-0201/proposed/`
- `collaboration/workstreams/WP-0202/proposed/`
- `collaboration/workstreams/WP-0204/proposed/`
- `collaboration/workstreams/WP-0205/proposed/`
- `collaboration/workstreams/WP-0206/proposed/`
- `collaboration/workstreams/WP-0208/proposed/`
- `collaboration/workstreams/WP-0209/proposed/`
- `collaboration/workstreams/WP-0210/proposed/`

## Revert instructions
1. Revert the WP-0212 commit with `git revert <commit>` if merged.
2. If reverting manually before merge, delete the installed `src/estate/core/office_*actions.py` files and matching `tests/test_office_*actions.py` files.
3. Rerun `PYTHONPATH=src pytest tests/test_steward_command_center.py -q` and `PYTHONPATH=src python -m estate.cli.main validation-production-readiness --json`.

## Generated/runtime artifacts
Runtime outputs under `runtime/steward/`, `runtime/validation/`, and `runtime/steward/exports/` may be regenerated or ignored.

## Partial install risks
Rolling back only later phases can leave tests or imports referring to removed metadata modules; revert by phase or whole commit.
