# Post-install Validation

- `python -m pytest collaboration/workstreams/WP-052{2,3,4,5,6,7,8,9}/staged/test_*.py collaboration/workstreams/WP-0530/staged/test_*.py` - 41 passed.
- `python -m pytest tests/test_office_executive_workspace.py tests/test_office_guided_actions.py tests/test_office_actionable_notifications.py tests/test_office_resident_presence.py tests/test_office_workspace_personalization.py tests/test_office_unified_search.py tests/test_office_operational_timeline.py tests/test_office_decision_support.py tests/test_office_operational_workflows.py` - 41 passed.
- `python -m pytest tests/test_office_end_to_end_regression.py` - 3 passed.
- `python -m py_compile ...` for all installed modules - passed.
