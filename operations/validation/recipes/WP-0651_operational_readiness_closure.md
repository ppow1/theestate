# WP-0651 Operational Readiness Closure Validation Recipe

This recipe validates the canonical `estate.core.operational_readiness_closure` controller in place.

Required commands:

1. `PYTHONPATH=src python -m pytest tests/test_operational_readiness_closure.py -q`
2. `PYTHONPATH=src python -m py_compile src/estate/core/operational_readiness_closure.py src/estate/core/operations_runtime.py src/estate/core/office_command_surface.py src/estate/cli/main.py`
3. Live production acceptance must be executed against the declared Windows Estate operational target before production readiness is claimed. The controller records live-target evidence under `runtime/operational_readiness/evidence/<case_id>/` and does not infer deployment, activation, validation, or observation from controller-local state.

Authority boundaries: no force reset, no force push, no discarded local work, no arbitrary generated shell execution, no speculative repair, no automatic institutional acceptance, and no duplicate Estate institution.
